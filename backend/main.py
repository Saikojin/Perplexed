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

class GuessRequest(BaseModel):
    riddle_id: int
    guess: str
    time_remaining: int = 0
    guesses_used: int = 0

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
        
        token = create_access_token(data={"sub": str(row['id'])})
        
        # Log active model
        model_status = llm_engine.get_status()
        print(f"User '{row['username']}' logged in. Active Model: {model_status.get('model', 'Unknown')}")
        
        return {
            "token": token,
            "user": {"id": row['id'], "username": row['username']}
        }

@app.get("/api/auth/me")
async def get_me(user = Depends(get_current_user)):
    return {
        "id": user['id'],
        "username": user['username'],
        "premium": False,
        "total_score": 0, # TODO: implement score summation
        "settings": {}
    }

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
    # Mocking friends for now as we don't have friend relationship table
    return [{"username": user['username'], "total_score": user['total_score'] if 'total_score' in user.keys() else 0}]

@app.patch("/api/user/settings")
async def update_settings(request: Request, user = Depends(get_current_user), db: aiosqlite.Connection = Depends(get_db)):
    # Accept any settings dict
    body = await request.json()
    
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
                    "active": status['model'] == name
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
        print(f"No active riddle found. Genering NEW one for {user['username']}...")
        gen = llm_engine.generate_riddle(request.difficulty)
        print(f"Generated content: {gen}")
        
        # Insert into riddles (we treat riddles table as a pool, but here we just add to it)
        await db.execute("INSERT INTO riddles (content, answer, difficulty, date_for) VALUES (?, ?, ?, ?)",
                         (gen['riddle'], gen['answer'], request.difficulty, today))
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
    
    # Logic
    is_correct = guess_text.lower().strip() == riddle['answer'].lower().strip()
    status_val = "solved" if is_correct else "playing"
    
    # Calculate score (Mock)
    score = 0
    if is_correct:
        score = 100 # Simplified
    
    guess_entry = {"word": guess_text, "correct": is_correct}
    guesses.append(guess_entry)
    
    guess_map = {"easy": 5, "medium": 4, "hard": 3, "very_hard": 2, "insane": 1}
    max_guesses = guess_map.get(riddle['difficulty'], 3)
    
    if not is_correct and len(guesses) >= max_guesses:
        status_val = "failed"

    await db.execute("UPDATE user_progress SET guesses = ?, status = ? WHERE user_id = ? AND riddle_id = ?",
                     (json.dumps(guesses), status_val, user['id'], riddle_id))
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
