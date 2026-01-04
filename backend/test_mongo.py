"""Test MongoDB connection."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def _test_mongo_async():
    """Async logic to connect to MongoDB and ping it."""
    try:
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        
        logger.info("Testing ping...")
        await client.admin.command('ping')
        
        logger.info("MongoDB connection successful!")
        
        # Try to access our database
        db = client.roddle
        logger.info("Listing collections in roddle database...")
        collections = await db.list_collection_names()
        logger.info(f"Collections: {collections}")
        
    except Exception as e:
        logger.error(f"MongoDB error: {e}")
        raise


def test_mongo():
    """Synchronous pytest-friendly wrapper that runs the async test logic."""
    asyncio.run(_test_mongo_async())


if __name__ == '__main__':
    asyncio.run(_test_mongo_async())