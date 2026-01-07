import aiosqlite
import json
import os

DB_NAME = "roddle.db"

# FastAPI Dependency
async def get_db():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        yield db

# Startup Init (Uses connect directly)
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                total_score INTEGER DEFAULT 0,
                premium BOOLEAN DEFAULT 0,
                settings TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migration: Ensure premium column exists for existing tables
        try:
            await db.execute("ALTER TABLE users ADD COLUMN premium BOOLEAN DEFAULT 0")
        except Exception:
            pass

        # Migration: Ensure settings column exists
        try:
            await db.execute("ALTER TABLE users ADD COLUMN settings TEXT DEFAULT '{}'")
        except Exception:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS riddles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                answer TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                date_for DATE,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Migration: Ensure user_id column exists for existing riddles table
        try:
            await db.execute("ALTER TABLE riddles ADD COLUMN user_id INTEGER")
        except Exception:
            pass
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id INTEGER,
                riddle_id INTEGER,
                guesses TEXT,  -- JSON list of guesses
                status TEXT,   -- 'playing', 'solved', 'failed'
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, riddle_id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(riddle_id) REFERENCES riddles(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending', -- pending, accepted, rejected
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(sender_id) REFERENCES users(id),
                FOREIGN KEY(receiver_id) REFERENCES users(id),
                UNIQUE(sender_id, receiver_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS friends (
                user_id INTEGER,
                friend_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, friend_id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(friend_id) REFERENCES users(id)
            )
        """)
        await db.commit()
