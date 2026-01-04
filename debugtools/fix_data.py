import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_user():
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['roddle']
    
    # Get user
    user = await db.users.find_one({"username": "test13"})
    if not user:
        print("User test13 not found")
        return

    # Find the problematic progress
    # We want to move 'day 11' (which was played yesterday) to 'day 10'
    res = await db.daily_progress.update_one(
        {"user_id": user['id'], "day": 11, "month": "2025-12"},
        {"$set": {"day": 10}}
    )
    
    print(f"Updated {res.modified_count} records for test13 (Day 11 -> Day 10)")
    
    # Also need to update the SCORE record associated with it?
    # Scores table has 'day' and 'month'.
    res_score = await db.scores.update_many(
        {"user_id": user['id'], "day": 11, "month": "2025-12"},
        {"$set": {"day": 10}}
    )
    print(f"Updated {res_score.modified_count} score records")
    
    # And the RIDDLE itself? db.riddles
    # The system looks for an ACTIVE riddle to resume.
    # If they completed it, it's fine.
    # If we move the riddle record to day 10, then query for day 11 will return None -> New Generation.
    res_riddle = await db.riddles.update_many(
        {"user_id": user['id'], "day": 11, "month": "2025-12"},
        {"$set": {"day": 10}}
    )
    print(f"Updated {res_riddle.modified_count} riddle records")

    client.close()

if __name__ == "__main__":
    asyncio.run(fix_user())
