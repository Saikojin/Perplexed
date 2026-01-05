
import asyncio
import aiohttp
import logging
import sys

# Configure logging to show everything
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger("test_ollama")

async def check_ollama():
    url = "http://127.0.0.1:11434/api/tags"
    logger.info(f"Attempting to connect to: {url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                logger.info(f"Response Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Response Data: {data}")
                    return True
                else:
                    logger.error(f"Failed with status: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False

async def generate_riddle():
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "neural-chat",
        "prompt": "Say hello",
        "stream": False
    }
    logger.info(f"Attempting to POST to: {url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                logger.info(f"Response Status: {response.status}")
                text = await response.text()
                logger.info(f"Response Text: {text}")
    except Exception as e:
        logger.error(f"Generation failed: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    print("="*50)
    print("TESTING OLLAMA CONNECTION")
    print("="*50)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(check_ollama())
    loop.run_until_complete(generate_riddle())
