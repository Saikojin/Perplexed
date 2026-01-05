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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS riddles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                answer TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                date_for DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
        await db.commit()
