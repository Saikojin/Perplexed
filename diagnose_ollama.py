
import asyncio
import os
import logging
from backend.ollama_llm import OllamaLLM

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose():
    print("Diagnosis Starting...")
    
    # 1. Test Environment Variable
    model_env = os.environ.get('OLLAMA_MODEL', 'neural-chat')
    print(f"Environment OLLAMA_MODEL: '{model_env}'")
    
    # 2. Initialize OllamaLLM
    llm = OllamaLLM(model=model_env)
    print(f"OllamaLLM initialized with model: '{llm.model}'")
    
    # 3. Force Availability Check
    print("Checking availability...")
    is_available = await llm.is_available()
    print(f"Is Available: {is_available}")
    
    # 4. If false, replicate the check logic manually to see why
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{llm.base_url}/api/tags") as response:
            if response.status == 200:
                data = await response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                print(f"Raw Models from API: {models}")
                
                check = any(llm.model in m for m in models)
                print(f"Check 'model in m': {check}")
                
                check_exact = options = any(m == llm.model or m == f"{llm.model}:latest" for m in models)
                print(f"Check exact/latest match: {check_exact}")

if __name__ == "__main__":
    # Add backend to path so imports work
    import sys
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    
    asyncio.run(diagnose())
