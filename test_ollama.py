import asyncio
import sys
sys.path.insert(0, 'D:\\DevWorkspace\\Roddle\\backend')

from ollama_llm import OllamaLLM

async def test():
    print("Testing Ollama connection...")
    llm = OllamaLLM()
    
    # Test availability
    available = await llm.is_available()
    print(f"Ollama available: {available}")
    
    if available:
        print("\nGenerating test riddle...")
        riddle = await llm.generate_riddle("easy")
        print(f"Result: {riddle}")
    else:
        print("Ollama not available!")

if __name__ == "__main__":
    asyncio.run(test())
