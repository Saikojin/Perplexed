from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, date, timedelta, timezone as dt_timezone
import aiosqlite
import json
import os
from typing import Optional, List, Dict
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database import init_db, get_db
from llm import llm_engine

app = FastAPI(title="Roddle Standalone")

from passlib.context import CryptContext

# Config
SECRET_KEY = "dev_secret_standalone_key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# --- Models ---
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class RiddleRequest(BaseModel):
    difficulty: str
    theme: Optional[str] = None
    seed: Optional[int] = None

class GuessRequest(BaseModel):
    riddle_id: int
    guess: str
    time_remaining: int = 0
    guesses_used: int = 0
    
class FriendRequest(BaseModel):
    friend_username: str

class FriendAction(BaseModel):
    request_id: int

# --- Auth Helpers ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(dt_timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: aiosqlite.Connection = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
        user = await cursor.fetchone()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user

# --- Startup ---
@app.on_event("startup")
async def startup_event():
    await init_db()

# --- Routes ---

@app.post("/api/auth/register")
async def register(user: UserCreate, db: aiosqlite.Connection = Depends(get_db)):
    import re
    # Validate Username
    if not re.match(r"^[a-zA-Z0-9]+$", user.username):
        raise HTTPException(status_code=400, detail="Username must contain only letters and numbers")
        
    # Validate Password
    # "letters, numbers, one uppercase, and a symbol from the following list: /\?!.><[]"
    # Note: Regex needs to allow all valid chars (letters, numbers, specified symbols) AND enforce presence of specific types.
    # Allowed chars: [a-zA-Z0-9/\\?!.><\[\]]
    # Requirements: At least one uppercase [A-Z], one digit [0-9], one symbol [/\?!.><\[\]]
    
    allowed_pattern = r"^[a-zA-Z0-9/\\?!.><\[\]]+$"
    if not re.match(allowed_pattern, user.password):
        raise HTTPException(status_code=400, detail="Password contains invalid characters. Allowed: letters, numbers, /\\?!.><[]")
        
    if not re.search(r"[A-Z]", user.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r"[0-9]", user.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")
    if not re.search(r"[/\\?!.><\[\]]", user.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character: /\\?!.><[]")

    try:
        # Check existing
        async with db.execute("SELECT id FROM users WHERE username = ?", (user.username,)) as cursor:
            if await cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username already exists")
                
        await db.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", 
                         (user.username, get_password_hash(user.password))) 
        await db.commit()
        
        # Determine ID
        async with db.execute("SELECT id, username FROM users WHERE username = ?", (user.username,)) as cursor:
            new_user = await cursor.fetchone()
            
        token = create_access_token(data={"sub": str(new_user['id'])})
        
        # Log active model
        model_status = llm_engine.get_status()
        print(f"User '{new_user['username']}' registered. Active Model: {model_status.get('model', 'Unknown')}")
        
        return {
            "token": token,
            "user": {"id": new_user['id'], "username": new_user['username']}
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
async def login(user: UserLogin, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM users WHERE username = ?", (user.username,)) as cursor:
        row = await cursor.fetchone()
        if not row or not verify_password(user.password, row['hashed_password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        settings = {}
        if row['settings']:
            try:
                settings = json.loads(row['settings'])
            except: 
                pass

        # Apply preferred model if set
        warning = None
        if settings.get('preferred_model'):
            model_name = settings['preferred_model']
            success = llm_engine.set_active_model(model_name)
            if not success:
               warning = f"Preferred model '{model_name}' could not be loaded. Switched to default."
               # potentially clear the preference effectively in memory or just warn
        
        token = create_access_token(data={"sub": str(row['id'])})
        
        # Log active model
        model_status = llm_engine.get_status()
        print(f"User '{row['username']}' logged in. Active Model: {model_status.get('model', 'Unknown')}")
        
        return {
            "token": token,
            "user": {
                "id": row['id'], 
                "username": row['username'],
                "total_score": row['total_score'],
                "premium": bool(row['premium']),
                "settings": settings
            },
            "warning": warning
        }

@app.get("/api/auth/me")
async def get_me(user = Depends(get_current_user)):
    settings = {}
    if user['settings']:
        try:
            settings = json.loads(user['settings'])
        except:
            pass
            
    return {
        "id": user['id'],
        "username": user['username'],
        "premium": bool(user['premium']),
        "total_score": user['total_score'],
        "settings": settings
    }

@app.post("/api/premium/unlock")
async def unlock_premium(user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("UPDATE users SET premium = 1 WHERE id = ?", (user['id'],))
    await db.commit()
    print(f"User {user['username']} unlocked premium!")
    return {"success": True}

@app.get("/api/riddles/daily-status")
async def get_daily_status(user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    difficulties = ["easy", "medium", "hard", "very_hard", "insane"]
    status_map = {}
    today = date.today().isoformat()

    # Check progress for each difficulty
    async with db.execute("SELECT r.difficulty, up.status FROM user_progress up JOIN riddles r ON up.riddle_id = r.id WHERE up.user_id = ? AND r.date_for = ?", (user['id'], today)) as cursor:
        rows = await cursor.fetchall()
        progress_dict = {row['difficulty']: row['status'] for row in rows}

    for diff in difficulties:
        # Determine if accessible (premium check normally)
        accessible = True 
        p_status = progress_dict.get(diff)
        
        status_map[diff] = {
            "accessible": accessible,
            "completed": p_status == "solved" or p_status == "failed", # Treat failed as completed for day? Or just solved?
            "started": p_status == "playing",
            "locked": not accessible
        }
        
    return {
        "day": date.today().day,
        "month": date.today().strftime("%Y-%m"),
        "status": status_map,
        "needs_generation": False
    }

@app.get("/api/leaderboard/global")
async def get_global_leaderboard(db: aiosqlite.Connection = Depends(get_db)):
    # Simple score based on user table (needs total_score Logic elsewhere really, but for now just returning users)
    # We didn't implement total_score incrementing in main.py yet, let's fix that in submit_guess too.
    async with db.execute("SELECT username, total_score FROM users ORDER BY total_score DESC LIMIT 10") as cursor:
        users = await cursor.fetchall()
    return [{"username": u['username'], "total_score": u['total_score'] or 0} for u in users]

@app.get("/api/leaderboard/friends")
async def get_friends_leaderboard(user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    # Get friends IDs
    async with db.execute("SELECT friend_id FROM friends WHERE user_id = ?", (user['id'],)) as cursor:
        rows = await cursor.fetchall()
        friend_ids = [row['friend_id'] for row in rows]
    
    # Always include self
    friend_ids.append(user['id'])
    
    if not friend_ids:
        return [{"username": user['username'], "total_score": user['total_score'] or 0}]

    placeholders = ",".join("?" * len(friend_ids))
    async with db.execute(f"SELECT username, total_score FROM users WHERE id IN ({placeholders}) ORDER BY total_score DESC", tuple(friend_ids)) as cursor:
        users = await cursor.fetchall()
        
    return [{"username": u['username'], "total_score": u['total_score'] or 0} for u in users]

@app.post("/api/friends/request")
async def send_friend_request(req: FriendRequest, user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    # Check target user exists
    async with db.execute("SELECT id FROM users WHERE username = ?", (req.friend_username,)) as cursor:
        target = await cursor.fetchone()
        if not target:
            raise HTTPException(404, "User not found")
        if target['id'] == user['id']:
             raise HTTPException(400, "Cannot add yourself")
             
    target_id = target['id']
    
    # Check existing request or friendship
    # Check if already friends
    async with db.execute("SELECT 1 FROM friends WHERE user_id = ? AND friend_id = ?", (user['id'], target_id)) as cursor:
        if await cursor.fetchone():
            raise HTTPException(400, "Already friends")

    # Check pending request (outgoing or incoming)
    async with db.execute("SELECT 1 FROM friend_requests WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)", 
                          (user['id'], target_id, target_id, user['id'])) as cursor:
        if await cursor.fetchone():
             raise HTTPException(400, "Request already pending")

    await db.execute("INSERT INTO friend_requests (sender_id, receiver_id) VALUES (?, ?)", (user['id'], target_id))
    await db.commit()
    return {"success": True}

@app.get("/api/friends/requests/pending")
async def get_pending_requests(user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("""
        SELECT fr.id, u.username as sender_username 
        FROM friend_requests fr
        JOIN users u ON fr.sender_id = u.id
        WHERE fr.receiver_id = ? AND fr.status = 'pending'
    """, (user['id'],)) as cursor:
        reqs = await cursor.fetchall()
    return [{"id": r['id'], "sender_username": r['sender_username']} for r in reqs]

@app.post("/api/friends/requests/accept")
async def accept_friend_request(action: FriendAction, user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    # Verify request exists and is for me
    async with db.execute("SELECT sender_id, receiver_id FROM friend_requests WHERE id = ? AND receiver_id = ? AND status = 'pending'", (action.request_id, user['id'])) as cursor:
        req = await cursor.fetchone()
        if not req:
            raise HTTPException(404, "Request not found")
            
    sender_id = req['sender_id']
    me_id = user['id']
    
    # Add bidirectional friendship
    await db.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (me_id, sender_id))
    await db.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (sender_id, me_id))
    
    # Update request status -> accepted (or delete it. Let's delete to keep clean? Or keep history. Let's delete for simplicity or set accepted)
    # Keeping history is nice, but removing is cleaner for uniqueness if they unfriend later.
    # User asked for "manage" requests. Let's just delete the request row once accepted to avoid unique constraint issues if re-added later.
    await db.execute("DELETE FROM friend_requests WHERE id = ?", (action.request_id,))
    await db.commit()
    return {"success": True}

@app.post("/api/friends/requests/reject")
async def reject_friend_request(action: FriendAction, user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("DELETE FROM friend_requests WHERE id = ? AND receiver_id = ?", (action.request_id, user['id'])) as cursor:
        if cursor.rowcount == 0:
             raise HTTPException(404, "Request not found")
    await db.commit()
    return {"success": True}

@app.patch("/api/user/settings")
async def update_settings(request: Request, user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    # Accept any settings dict
    body = await request.json()
    
    # Save to DB
    await db.execute("UPDATE users SET settings = ? WHERE id = ?", (json.dumps(body), user['id']))
    await db.commit()
    
    # Check if preferred_model changed
    preferred = body.get("preferred_model")
    if preferred:
        print(f"Switching model to: {preferred}")
        llm_engine.set_active_model(preferred)
        
    return {"message": "Settings updated", "settings": body}

@app.get("/api/models/available")
async def get_models():
    status = llm_engine.get_status()
    models = []
    
    # Scan models directory for .gguf files
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    if os.path.exists(models_dir):
        for f in os.listdir(models_dir):
            if f.endswith(".gguf"):
                name = f.replace(".gguf", "")
                models.append({
                    "name": name,
                    "type": "local",
                    "details": "Embedded GGUF",
                    "active": status['model'] == f
                })
                
    # If list empty but engine loaded something (e.g. legacy model.gguf), add it
    if not models and status['status'] == 'loaded':
         models.append({"name": "legacy-model", "type": "local", "details": "Embedded GGUF", "active": True})
         
    return models

@app.post("/api/models/pull")
async def pull_model(request: Request):
    # Trigger download
    # Make async in background? For now blocking is easier to code but bad UX.
    # Let's just mock the trigger or try to run in thread.
    body = await request.json()
    model_name = body.get("model_name") or body.get("model") or "tinyllama"
    
    import threading
    threading.Thread(target=llm_engine.download_model, args=(model_name,)).start()
    return {"message": f"Model '{model_name}' download started. Check backend logs."}

@app.get("/api/models/download-status")
async def get_download_status():
    return llm_engine.get_download_status()



@app.post("/api/riddle/generate")
async def generate_riddle(request: RiddleRequest, user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    # Check if this user has an ACTIVE (playing) riddle for this difficulty
    today = date.today().isoformat()
    logging.info(f"Generating request for user {user['username']} - Difficulty: {request.difficulty}")

    riddle_id = None
    
    # query user progress for 'playing' status on this difficulty
    # Note: user_progress links user to riddle. We need to join with riddles to check difficulty.
    async with db.execute("""
        SELECT r.id FROM user_progress up 
        JOIN riddles r ON up.riddle_id = r.id 
        WHERE up.user_id = ? AND r.difficulty = ? AND up.status = 'playing'
    """, (user['id'], request.difficulty)) as cursor:
        active_riddle = await cursor.fetchone()
        
    if active_riddle:
        # Resume existing
        print(f"Resuming active riddle ID: {active_riddle['id']}")
        riddle_id = active_riddle['id']
    else:
        # Generate NEW unique riddle
        import uuid
        request_id = str(uuid.uuid4())
        print(f"No active riddle found. Genering NEW one for {user['username']}... (ReqID: {request_id})")
        gen = llm_engine.generate_riddle(request.difficulty, theme=request.theme, seed=request.seed, request_id=request_id)
        print(f"Generated content: {gen}")
        
        # Insert into riddles (we treat riddles table as a pool, but here we just add to it)
        await db.execute("INSERT INTO riddles (content, answer, difficulty, date_for, user_id) VALUES (?, ?, ?, ?, ?)",
                         (gen['riddle'], gen['answer'], request.difficulty, today, user['id']))
        await db.commit()
        
        # Get the ID of the just inserted riddle
        async with db.execute("SELECT last_insert_rowid()") as cursor:
             row = await cursor.fetchone()
             riddle_id = row[0]
             
    # Create or Get progress (if we just created it, it won't exist. If we resumed, it exists)
    async with db.execute("SELECT * FROM user_progress WHERE user_id = ? AND riddle_id = ?", (user['id'], riddle_id)) as cursor:
        progress = await cursor.fetchone()
        
    if not progress:
        await db.execute("INSERT INTO user_progress (user_id, riddle_id, guesses, status) VALUES (?, ?, ?, ?)",
                         (user['id'], riddle_id, "[]", "playing"))
        await db.commit()
        # Re-fetch progress
        async with db.execute("SELECT * FROM user_progress WHERE user_id = ? AND riddle_id = ?", (user['id'], riddle_id)) as cursor:
            progress = await cursor.fetchone()
    
    # Return details expected by legacy frontend
    # It expects: riddle_id, riddle, answer_length, max_guesses
    # Fetch content
    async with db.execute("SELECT * FROM riddles WHERE id = ?", (riddle_id,)) as cursor:
        riddle_data = await cursor.fetchone()
        
    guess_map = {"easy": 5, "medium": 4, "hard": 3, "very_hard": 2, "insane": 1}
    
    return {
        "riddle_id": riddle_id,
        "riddle": riddle_data['content'],
        "answer_length": len(riddle_data['answer']),
        "max_guesses": guess_map.get(request.difficulty, 3),
        "difficulty": request.difficulty,
        "day": date.today().day,
        "month": date.today().strftime("%Y-%m")
    }

@app.post("/api/riddle/guess")
async def submit_guess(request: GuessRequest, user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    riddle_id = request.riddle_id
    guess_text = request.guess
    
    async with db.execute("SELECT * FROM riddles WHERE id = ?", (riddle_id,)) as cursor:
        riddle = await cursor.fetchone()
        if not riddle:
             raise HTTPException(404, "Riddle not found")

    async with db.execute("SELECT * FROM user_progress WHERE user_id = ? AND riddle_id = ?", (user['id'], riddle_id)) as cursor:
        progress = await cursor.fetchone()
    
    guesses = json.loads(progress['guesses']) if progress else []
    
    
    if progress and progress['status'] in ['solved', 'failed']:
         return {"correct": progress['status'] == 'solved', "answer": riddle['answer'], "score": 0, "breakdown": {"base": 0}}

    # Logic
    is_correct = guess_text.lower().strip() == riddle['answer'].lower().strip()
    status_val = "solved" if is_correct else "playing"
    
    # Calculate score
    # Formula: Difficulty base + (time_remaining_fraction * difficulty base) + remaining guesses (100 each)
    score = 0
    if is_correct:
        diff_base_map = {
            "easy": 100, 
            "medium": 200, 
            "hard": 300, 
            "very_hard": 400, 
            "insane": 500
        }
        base_points = diff_base_map.get(riddle['difficulty'], 100)
        
        # Max guesses for the difficulty
        guess_map = {"easy": 5, "medium": 4, "hard": 3, "very_hard": 2, "insane": 1}
        max_g = guess_map.get(riddle['difficulty'], 3)
        
        guesses_taken = len(guesses) # current list includes the just added correct guess
        guesses_remaining = max_g - guesses_taken
        
        # Assuming time_remaining is in seconds, and max time is 120 (hardcoded in frontend)
        # (hidden time remaining * difficulty base) -> Interpret as fraction of time left * base
        # But user said "(hidden time remaining * difficulty base)". If time is 60s, 60*100 = 6000. Huge.
        # Let's assume they might mean a small factor. 
        # Actually simplest interpretation: (time_remaining_seconds * base/100) or similar? 
        # User words: "(hidden time remaining * difficulty base)"
        # If I strictly follow: 120 * 100 = 12000. 
        # Maybe they mean: Base + (Time * Base). Let's implement literally but cap time if needed?
        # Maybe "Time" refers to a multiplier? No, Request has time_remaining.
        # Let's try: base + (request.time_remaining * base) + (remaining_guesses * 100)
        # Wait, if time_remaining is 100, and base is 100. 100 + 10000 + ... = 10100.
        # This seems intended for high scores.
        
        time_bonus = request.time_remaining * base_points
        guess_bonus = guesses_remaining * 100
        
        score = base_points + time_bonus + guess_bonus

    guess_entry = {"word": guess_text, "correct": is_correct}
    guesses.append(guess_entry)
    
    guess_map = {"easy": 5, "medium": 4, "hard": 3, "very_hard": 2, "insane": 1}
    max_guesses = guess_map.get(riddle['difficulty'], 3)
    
    if not is_correct and len(guesses) >= max_guesses:
        status_val = "failed"

    await db.execute("UPDATE user_progress SET guesses = ?, status = ? WHERE user_id = ? AND riddle_id = ?",
                     (json.dumps(guesses), status_val, user['id'], riddle_id))
                     
    if is_correct:
        print(f"User {user['username']} (ID: {user['id']}) solved riddle {riddle_id}.")
        print(f"Score Calc: Base {base_points} + TimeBonus {time_bonus} + GuessBonus {guess_bonus} = {score}")
        await db.execute("UPDATE users SET total_score = total_score + ? WHERE id = ?", (score, user['id']))
        print("User score updated in DB.")

    await db.commit()
    
    if is_correct:
        return {
            "correct": True,
            "answer": riddle['answer'],
            "score": score,
            "breakdown": {"base": score}
        }
    else:
        return {"correct": False, "answer": None if status_val == "playing" else riddle['answer']}


# --- Static Files ---
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {"message": "Perplexed Standalone API Running. Static files not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
