import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def inspect():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['roddle']
    
    username = "test12" # User mentioned in logs earlier, or test13? User said "test13" in text, but logged "test12" in error.
    # Let's check both or list all.
    
    print(f"Current UTC: {datetime.now(timezone.utc)}")
    print(f"Current Day (UTC): {datetime.now(timezone.utc).day}")
    
    users = await db.users.find({"username": {"$in": ["test12", "test13"]}}).to_list(10)
    for u in users:
        print(f"User: {u['username']} | ID: {u['id']}")
        
        # Check daily progress
        progress = await db.daily_progress.find({"user_id": u['id']}).sort("timestamp", -1).to_list(10)
        print("  Recent Progress:")
        for p in progress:
            print(f"    Diff: {p.get('difficulty')} | Day: {p.get('day')} | Month: {p.get('month')} | TS: {p.get('timestamp')}")
            
    client.close()

if __name__ == "__main__":
    asyncio.run(inspect())
