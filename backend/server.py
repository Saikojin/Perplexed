from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt

# Setup logging FIRST before any LLM imports
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Force file handler for debugging
file_handler = logging.FileHandler('server_debug.log', mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)
logger.info("!!! SERVER.PY LOADED - LOGGING TO server_debug.log !!!")
print("!!! SERVER.PY LOADED - VERSION: NO_FALLBACKS_ENABLED !!!", flush=True)

# LLM implementation selection with fallback chain:
# 1. Try Ollama (if available)
# 2. Fall back to local transformers model
# 3. Fall back to mock implementation
# Can be controlled via LLM_MODE env var:
# - 'ollama': try Ollama first, then local, then mock
# - 'local': use local transformers model (falls back to mock if unavailable)
# - 'mock': always use mock implementation
# Default: try Ollama first, then local, then mock

llm_mode = os.environ.get('LLM_MODE', 'ollama').lower()
ollama_model = os.environ.get('OLLAMA_MODEL', 'neural-chat').strip()
logger.info(f"LLM_MODE set to: {llm_mode}")
logger.info(f"OLLAMA_MODEL set to: '{ollama_model}'")

# Initialize LLM instances
# Global state handled by ModelManager
from model_manager import ModelManager

# Global state
model_manager = None

import hashlib
import asyncio
from cryptography.fernet import Fernet
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Load environment variables
dotenv_path = ROOT_DIR / '.env'
load_dotenv(dotenv_path)

# Global state (initialized in lifespan)
db = None
client = None
generation_lock = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle - connect to MongoDB on startup."""
    global db, client
    
    # Startup
    try:
        logger.info("Connecting to MongoDB on startup...")
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.getenv('DB_NAME', 'roddle')
        logger.info(f"MongoDB URL: {mongo_url}, Database: {db_name}")
        
        # Connect DB
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        await client.admin.command('ping')
        
        # Initialize Model Manager
        global model_manager
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        model_manager = ModelManager(ollama_url=ollama_url, default_model=ollama_model)
        logger.info("ModelManager initialized")
        
        yield  # Run app
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        # Cleanup
        if client:
            logger.info("Closing MongoDB connection...")
            client.close()
            logger.info("MongoDB connection closed")

# Create the main app with lifespan
app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'dev_secret_replace_in_production')
ALGORITHM = "HS256"

# Encryption setup
encryption_key = os.getenv('ENCRYPTION_KEY', 'dev_encryption_key_replace_in_production')[:32].ljust(32, ' ')
ENCRYPTION_KEY = base64.urlsafe_b64encode(encryption_key.encode())
cipher_suite = Fernet(ENCRYPTION_KEY)

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    user = await db.users.find_one({"id": payload['user_id']}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def encrypt_text(text: str) -> str:
    return cipher_suite.encrypt(text.encode()).decode()

def decrypt_text(encrypted: str) -> str:
    return cipher_suite.decrypt(encrypted.encode()).decode()

def generate_riddle_id(user_id: str) -> str:
    """Generate unique riddle ID based on user_id + random + timestamp"""
    timestamp = datetime.now(timezone.utc).isoformat()
    random_val = str(uuid.uuid4())
    combined = f"{user_id}-{random_val}-{timestamp}"
    return hashlib.sha256(combined.encode()).hexdigest()

async def generate_riddle_with_ai(difficulty: str, theme: str = "default", preferred_model: str = None, api_keys: dict = {}) -> tuple:
    """Delegate to ModelManager"""
    return await model_manager.generate_riddle(difficulty, theme, preferred_model, api_keys)


async def ensure_monthly_structure(month_str: str):
    """Ensure the monthly_riddles document exists for the given month with empty lists."""
    existing = await db.monthly_riddles.find_one({"month": month_str})
    if existing:
        return existing
        
    difficulties = ["easy", "medium", "hard", "very_hard", "insane"]
    monthly_riddles = {
        "month": month_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "riddles": {diff: [None] * 31 for diff in difficulties} # Pre-fill with None
    }
    
    await db.monthly_riddles.insert_one(monthly_riddles)
    logger.info(f"Created empty monthly structure for {month_str}")
    return monthly_riddles

async def generate_daily_riddles(month_str: str, day: int):
    """Generate riddles for a specific day for all difficulties."""
    # Use global lock to prevent race conditions
    global generation_lock
    if generation_lock is None:
        generation_lock = asyncio.Lock()
        
    async with generation_lock:
        # Double-check: did another request already generate them?
        monthly = await db.monthly_riddles.find_one({"month": month_str})
        if monthly:
            try:
                # If "easy" riddle exists for this day, assume batch was generated
                if monthly["riddles"]["easy"][day-1] is not None:
                    logger.info(f"Riddles for {month_str} day {day} already exist. Skipping generation.")
                    return True
            except (KeyError, IndexError):
                pass
                
        logger.info(f"Generating daily riddles for {month_str} day {day}...")
        
        await ensure_monthly_structure(month_str)
        
        difficulties = ["easy", "medium", "hard", "very_hard", "insane"]
        
        async def generate_one(difficulty):
            # Fallback handling removed to force error visibility
            riddle_text, answer = await generate_riddle_with_ai(difficulty)
            encrypted_riddle = encrypt_text(riddle_text)
            encrypted_answer = encrypt_text(answer)
            
            return difficulty, {
                "day": day,
                "encrypted_riddle": encrypted_riddle,
                "encrypted_answer": encrypted_answer,
                "answer_length": len(answer)
            }

        tasks = [generate_one(diff) for diff in difficulties]
        results = await asyncio.gather(*tasks)
        
        # Update database
        updates = {}
        for difficulty, riddle_data in results:
            # MongoDB arrays are 0-indexed, day is 1-indexed
            updates[f"riddles.{difficulty}.{day-1}"] = riddle_data
            
        await db.monthly_riddles.update_one(
            {"month": month_str},
            {"$set": updates}
        )
        
        logger.info(f"Successfully generated riddles for {month_str} day {day}")
        return True

def get_game_time():
    """Get current game time (UTC - 8 hours for PST alignment)"""
    return datetime.now(timezone.utc) - timedelta(hours=8)

def get_current_day_of_month():
    """Get current day of month (1-31) based on Game Time"""
    return get_game_time().day

# Models
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str
    username: str
    premium: bool = False
    total_score: int = 0
    friends: List[str] = []
    settings: dict = {}
    created_at: str

class RiddleRequest(BaseModel):
    difficulty: str

class GuessRequest(BaseModel):
    riddle_id: str
    guess: str
    time_remaining: int
    guesses_used: int

class ScoreSubmit(BaseModel):
    riddle_id: str
    difficulty: str
    score: int
    time_remaining: int
    guesses_used: int

class UserSettings(BaseModel):
    ui_color_primary: Optional[str] = None
    ui_color_accent: Optional[str] = None
    background_url: Optional[str] = None
    theme: str = "default"
    preferred_model: Optional[str] = None
    api_keys: Optional[Dict[str, str]] = None

class PullModelRequest(BaseModel):
    model_name: str

class AddFriendRequest(BaseModel):
    friend_username: str

# Routes
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    existing = await db.users.find_one({"username": user_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "username": user_data.username,
        "password": hash_password(user_data.password),
        "premium": False,
        "total_score": 0,
        "friends": [],
        "settings": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    token = create_token(user_id)
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "username": user_data.username,
            "premium": False,
            "total_score": 0,
            "settings": {}
        }
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"username": credentials.username})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'])
    
    return {
        "token": token,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "premium": user.get('premium', False),
            "total_score": user.get('total_score', 0),
            "settings": user.get('settings', {})
        }
    }

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": user['id'],
        "username": user['username'],
        "premium": user.get('premium', False),
        "total_score": user.get('total_score', 0),
        "settings": user.get('settings', {}),
        "friends": user.get('friends', [])
    }

@api_router.post("/riddle/generate")
async def generate_riddle(request: RiddleRequest, user: dict = Depends(get_current_user)):
    # Check if user can access this difficulty
    premium_difficulties = ["very_hard", "insane"]
    if request.difficulty in premium_difficulties and not user.get('premium', False):
        raise HTTPException(status_code=403, detail="Premium required for this difficulty")
    
    # Get current day and month
    current_day = get_current_day_of_month()
    current_month = get_game_time().strftime("%Y-%m")
    
    # Check if user already COMPLETED this difficulty today
    played_today = await db.daily_progress.find_one({
        "user_id": user['id'],
        "month": current_month,
        "day": current_day,
        "difficulty": request.difficulty
    })
    
    if played_today:
        raise HTTPException(
            status_code=400, 
            detail=f"You've already played {request.difficulty} today! Come back tomorrow for a new riddle."
        )
    
    # Check for ACTIVE (unfinished) riddle in db.riddles
    # We now support PER-USER unique riddles instead of a global shared cache
    existing_riddle = await db.riddles.find_one({
        "user_id": user['id'],
        "month": current_month,
        "day": current_day,
        "difficulty": request.difficulty
    })
    
    riddle_text = None
    riddle_id = None
    answer_length = 0
    
    if existing_riddle and "encrypted_riddle" in existing_riddle:
        # Resume existing session
        logger.info(f"Resuming existing personalized riddle for user {user['id']}")
        print(f"[CACHE HIT] Resuming Personal Riddle for User: {user['username']}", flush=True)
        riddle_id = existing_riddle["id"]
        riddle_text = decrypt_text(existing_riddle["encrypted_riddle"])
        answer_length = existing_riddle["answer_length"]
    else:
        # Generate NEW unique riddle for this user
        if existing_riddle:
             # Legacy doc without text? Delete it.
             await db.riddles.delete_one({"_id": existing_riddle["_id"]})
        
        logger.info(f"Generating new unique riddle for user {user['id']}...")
        print(f"[CACHE MISS] Generating Personal Riddle for User: {user['username']}", flush=True)
        
        try:
            # Extract theme and model
            user_theme = user.get('settings', {}).get('theme', 'default')
            preferred_model = user.get('settings', {}).get('preferred_model')
            
            # Verify premium for non-default themes
            if user_theme != 'default' and not user.get('premium', False):
                user_theme = 'default' # Fallback if not premium
                
            # Extract keys and decrypt them
            encrypted_keys = user.get('settings', {}).get('api_keys', {})
            decrypted_keys = {}
            for provider, key in encrypted_keys.items():
                try:
                    decrypted_keys[provider] = decrypt_text(key)
                except:
                    logger.error(f"Failed to decrypt key for {provider}")

            riddle_text, answer = await generate_riddle_with_ai(request.difficulty, theme=user_theme, preferred_model=preferred_model, api_keys=decrypted_keys)
        except HTTPException as e:
            # If Ollama fails, we should re-raise
            raise e
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate riddle")
        
        # Create new session
        riddle_id = generate_riddle_id(user['id'])
        encrypted_riddle = encrypt_text(riddle_text)
        encrypted_answer = encrypt_text(answer)
        answer_length = len(answer)
        
        riddle_doc = {
            "id": riddle_id,
            "user_id": user['id'],
            "month": current_month,
            "day": current_day,
            "difficulty": request.difficulty,
            "theme": user_theme,
            "encrypted_riddle": encrypted_riddle,   # NEW: Store riddle text!
            "encrypted_answer": encrypted_answer,
            "answer_length": answer_length,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.riddles.insert_one(riddle_doc)
    
    # Determine guesses allowed
    guess_map = {"easy": 5, "medium": 4, "hard": 3, "very_hard": 2, "insane": 1}
    max_guesses = guess_map.get(request.difficulty, 3)
    
    return {
        "riddle_id": riddle_id,
        "riddle": riddle_text,
        "answer_length": answer_length,
        "max_guesses": max_guesses,
        "difficulty": request.difficulty,
        "day": current_day,
        "month": current_month
    }

@api_router.post("/riddle/guess")
async def check_guess(request: GuessRequest, user: dict = Depends(get_current_user)):
    riddle = await db.riddles.find_one({"id": request.riddle_id})
    if not riddle:
        raise HTTPException(status_code=404, detail="Riddle not found")
    
    if riddle['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail="Not your riddle")
    
    # Decrypt answer
    correct_answer = decrypt_text(riddle['encrypted_answer'])
    
    # Always return answer so frontend can reveal it when needed
    is_correct = request.guess.upper() == correct_answer
    
    if is_correct:
        # Calculate score
        difficulty_multiplier = {"easy": 10, "medium": 20, "hard": 40, "very_hard": 80, "insane": 150}
        base_score = difficulty_multiplier.get(riddle['difficulty'], 20)
        
        time_bonus = request.time_remaining * 2
        guess_map = {"easy": 5, "medium": 4, "hard": 3, "very_hard": 2, "insane": 1}
        max_guesses = guess_map.get(riddle['difficulty'], 3)
        guesses_remaining = max_guesses - request.guesses_used
        guess_bonus = guesses_remaining * 50
        
        total_score = base_score + time_bonus + guess_bonus
        
        # Save score
        score_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user['id'],
            "username": user['username'],
            "riddle_id": request.riddle_id,
            "difficulty": riddle['difficulty'],
            "score": total_score,
            "time_remaining": request.time_remaining,
            "guesses_used": request.guesses_used,
            "month": riddle.get('month'),
            "day": riddle.get('day'),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.scores.insert_one(score_doc)
        
        # Mark daily progress as complete
        await db.daily_progress.insert_one({
            "user_id": user['id'],
            "month": riddle.get('month'),
            "day": riddle.get('day'),
            "difficulty": riddle['difficulty'],
            "completed": True,
            "score": total_score,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Update user total score
        await db.users.update_one(
            {"id": user['id']},
            {"$inc": {"total_score": total_score}}
        )
        
        return {
            "correct": True,
            "answer": correct_answer,
            "score": total_score,
            "breakdown": {
                "base": base_score,
                "time_bonus": time_bonus,
                "guess_bonus": guess_bonus
            }
        }
    
    return {"correct": False, "answer": correct_answer}

@api_router.get("/leaderboard/global")
async def get_global_leaderboard():
    # Get top users by total score
    users = await db.users.find(
        {},
        {"_id": 0, "username": 1, "total_score": 1}
    ).sort("total_score", -1).limit(100).to_list(100)
    
    return users

@api_router.get("/leaderboard/friends")
async def get_friends_leaderboard(user: dict = Depends(get_current_user)):
    friend_ids = user.get('friends', [])
    friend_ids.append(user['id'])  # Include self
    
    users = await db.users.find(
        {"id": {"$in": friend_ids}},
        {"_id": 0, "username": 1, "total_score": 1}
    ).sort("total_score", -1).to_list(100)
    
    return users

@api_router.post("/friends/add")
async def add_friend(request: AddFriendRequest, user: dict = Depends(get_current_user)):
    friend = await db.users.find_one({"username": request.friend_username})
    if not friend:
        raise HTTPException(status_code=404, detail="User not found")
    
    if friend['id'] == user['id']:
        raise HTTPException(status_code=400, detail="Cannot add yourself")
    
    # Add friend to both users
    await db.users.update_one(
        {"id": user['id']},
        {"$addToSet": {"friends": friend['id']}}
    )
    
    await db.users.update_one(
        {"id": friend['id']},
        {"$addToSet": {"friends": user['id']}}
    )
    
    return {"message": "Friend added successfully"}

@api_router.post("/premium/unlock")
async def unlock_premium(user: dict = Depends(get_current_user)):
    # Mock payment - in production, integrate real payment processor
    await db.users.update_one(
        {"id": user['id']},
        {"$set": {"premium": True}}
    )
    
    return {"message": "Premium unlocked!", "premium": True}

@api_router.get("/riddles/daily-status")
async def get_daily_status(user: dict = Depends(get_current_user)):
    """Get status of today's riddles for all difficulties"""
    current_day = get_current_day_of_month()
    current_month = get_game_time().strftime("%Y-%m")
    
    # Get user's completed riddles for today
    completed_today = await db.daily_progress.find({
        "user_id": user['id'],
        "month": current_month,
        "day": current_day
    }).to_list(100)
    
    # Get user's active (started) riddles for today
    active_today = await db.riddles.find({
        "user_id": user['id'],
        "month": current_month,
        "day": current_day
    }).to_list(100)
    
    completed_difficulties = {item['difficulty'] for item in completed_today}
    active_difficulties = {item['difficulty'] for item in active_today}
    
    difficulties = ["easy", "medium", "hard", "very_hard", "insane"]
    status = {}
    
    for diff in difficulties:
        can_access = diff not in ["very_hard", "insane"] or user.get('premium', False)
        status[diff] = {
            "accessible": can_access,
            "completed": diff in completed_difficulties,
            "started": diff in active_difficulties,
            "locked": not can_access
        }
    
    # We no longer rely on global batch generation.
    # Riddles are generated on-demand per user.
    # So "needs_generation" is always False to prevent the frontend from blocking interaction.
    
    return {
        "day": current_day,
        "month": current_month,
        "status": status,
        "needs_generation": False
    }

@api_router.post("/riddle/generate-daily")
async def trigger_daily_generation(user: dict = Depends(get_current_user)):
    """Trigger generation of riddles for today"""
    current_day = get_current_day_of_month()
    current_month = get_game_time().strftime("%Y-%m")
    
    await generate_daily_riddles(current_month, current_day)
    return {"message": "Daily riddles generated"}

@api_router.post("/admin/generate-monthly-riddles")
async def admin_generate_riddles():
    """Admin endpoint to manually trigger monthly riddle generation"""
    try:
        monthly_riddles = await generate_monthly_riddles()
        return {
            "message": "Monthly riddles generated successfully",
            "month": monthly_riddles["month"],
            "total_riddles": sum(len(riddles) for riddles in monthly_riddles["riddles"].values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/user/stats")
async def get_user_stats(user: dict = Depends(get_current_user)):
    scores = await db.scores.find({"user_id": user['id']}).to_list(1000)
    
    total_games = len(scores)
    avg_score = sum(s['score'] for s in scores) / total_games if total_games > 0 else 0
    
    difficulty_stats = {}
    for score in scores:
        diff = score['difficulty']
        if diff not in difficulty_stats:
            difficulty_stats[diff] = {"count": 0, "total_score": 0}
        difficulty_stats[diff]['count'] += 1
        difficulty_stats[diff]['total_score'] += score['score']
    
    return {
        "total_games": total_games,
        "total_score": user.get('total_score', 0),
        "average_score": int(avg_score),
        "difficulty_stats": difficulty_stats
    }

@api_router.get("/health")
async def health_check():
    """Health check endpoint with LLM status"""
    ollama_status = "unknown"
    try:
        models = await model_manager.get_available_models()
        ollama_status = "available" if models else "no_models"
    except:
        ollama_status = "unavailable"
    
    return {
        "status": "healthy",
        "llm_mode": llm_mode,
        "llm_status": {
            "ollama": ollama_status,
            "local": "removed",
            "mock": "available"
        },
        "database": "connected" if db is not None else "not_connected"
    }

@api_router.patch("/user/settings")
async def update_user_settings(settings: UserSettings, user: dict = Depends(get_current_user)):
    """Update user settings"""
    update_data = {}
    
    if settings.ui_color_primary is not None:
        update_data["settings.ui_color_primary"] = settings.ui_color_primary
    if settings.ui_color_accent is not None:
        update_data["settings.ui_color_accent"] = settings.ui_color_accent
    if settings.background_url is not None:
        update_data["settings.background_url"] = settings.background_url
    if settings.theme is not None:
        # Check premium for theme change
        if settings.theme != 'default' and not user.get('premium', False):
            raise HTTPException(status_code=403, detail="Premium required for this theme")
        update_data["settings.theme"] = settings.theme
        
    if settings.preferred_model is not None:
        update_data["settings.preferred_model"] = settings.preferred_model

    if settings.api_keys is not None:
        # Encrypt keys before storing
        for provider, key in settings.api_keys.items():
            if key: # only save if non-empty
                encrypted = encrypt_text(key)
                update_data[f"settings.api_keys.{provider}"] = encrypted

    if not update_data:
        return {"message": "No changes made"}
        
    await db.users.update_one(
        {"id": user['id']},
        {"$set": update_data}
    )
    
    return {"message": "Settings updated successfully"}

@api_router.get("/models/available")
async def get_models():
    """Get available Ollama models"""
    return await model_manager.get_available_models()

@api_router.post("/models/pull")
async def trigger_model_pull(request: PullModelRequest, user: dict = Depends(get_current_user)):
    """Trigger Ollama model pull"""
    # Only admins or premium users? Let's say anyone for now, or restriction? 
    # Todo didn't specify, but downloading can be heavy.
    success = await model_manager.pull_model(request.model_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to pull model")
    return {"message": f"Started pulling {request.model_name}"}

# Include router
app.include_router(api_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"]   # Allows all headers
)