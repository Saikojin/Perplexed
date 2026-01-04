import asyncio
import aiohttp
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__) # Will inherit file handler from server.py setup

class OllamaLLM:
    """Ollama LLM client for riddle generation"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "neural-chat"):
        self.base_url = base_url
        self.model = model
        self.timeout = aiohttp.ClientTimeout(total=120) # Increased timeout to 2 minutes
        
    async def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check if our model is available
                        models = [m.get("name", "") for m in data.get("models", [])]
                        print(f"[OllamaLLM] Checked availability. Available models: {models}", flush=True)
                        found = any(self.model in m for m in models)
                        if not found:
                            msg = f"Ollama model '{self.model}' not found in available models: {models}"
                            logger.warning(msg)
                            print(f"[OllamaLLM] WARNING: {msg}", flush=True)
                            # FORCE TRUE anyway to attempt generation - maybe the tag name is just different
                            print(f"[OllamaLLM] Proceeding despite model name mismatch.", flush=True)
                            return True 
                        return True
            return False
        except Exception as e:
            return False
    
    async def list_models(self) -> list:
        """List available models in Ollama"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("models", [])
            return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama library"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session: # Long timeout for pull
                logger.info(f"Pulling model {model_name}...")
                payload = {"name": model_name, "stream": False}
                async with session.post(f"{self.base_url}/api/pull", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'success':
                             logger.info(f"Successfully pulled {model_name}")
                             return True
                        # Ollama usually returns objects with 'status' like 'downloading' etc if stream=True
                        # If stream=False, it waits until done and returns final status?
                        # Actually Ollama API doc says stream=false returns final response.
                        logger.info(f"Pull response: {data}")
                        return True 
                    else:
                        logger.error(f"Failed to pull {model_name}: Status {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False

    async def generate_riddle(self, difficulty: str, instruction: Optional[str] = None) -> Optional[str]:
        """
        Generate a riddle using Ollama
        
        Args:
            difficulty: The difficulty level (easy, medium, hard, very_hard, insane)
            instruction: Optional custom instruction to use instead of default difficulty logic
            
        Returns:
            Formatted riddle string or None if generation fails
        """
        try:
            # Create prompt based on difficulty or custom instruction
            prompt = self._create_prompt(difficulty, instruction)
            
            # Call Ollama API
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "num_predict": 200
                    }
                }
                
                url = f"{self.base_url}/api/generate"
                msg = f"POSTing to Ollama: {url} with model {self.model}"
                logger.info(msg)
                print(f"[OllamaLLM] {msg}", flush=True) # Force print to stdout
                
                async with session.post(url, json=payload) as response:
                    print(f"[OllamaLLM] Received response status: {response.status}", flush=True)
                    if response.status != 200:
                        error_msg = f"Ollama API returned status {response.status}"
                        logger.error(error_msg)
                        print(f"[OllamaLLM] ERROR: {error_msg}", flush=True)
                        return None
                    
                    data = await response.json()
                    generated_text = data.get("response", "").strip()
                    print(f"[OllamaLLM] Received data length: {len(generated_text)}", flush=True)
                    print(f"[OllamaLLM] RAW RESPONSE TEXT: >>>{generated_text}<<<", flush=True)
                    
                    if not generated_text:
                        logger.error("Ollama returned empty response")
                        print("[OllamaLLM] ERROR: Empty response", flush=True)
                        return None
                    
                    # Parse and format the response
                    riddle = self._parse_riddle(generated_text)
                    return riddle
                    
        except asyncio.TimeoutError:
            logger.error("Ollama request timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating riddle with Ollama: {e}")
            return None
    
    def _create_prompt(self, difficulty: str, instruction: Optional[str] = None) -> str:
        """Create a prompt for riddle generation"""
        
        if instruction:
            user_msg = instruction
        else:
            difficulty_hints = {
                "easy": "simple and straightforward, suitable for children",
                "medium": "moderately challenging, requiring some thought",
                "hard": "challenging and clever, requiring creative thinking",
                "very_hard": "very difficult and tricky, with wordplay or misdirection",
                "insane": "extremely difficult, with complex wordplay and lateral thinking"
            }
            hint = difficulty_hints.get(difficulty, "moderately challenging")
            user_msg = f"Generate a {hint} riddle. Do NOT use the riddle about 'keys but no locks' (keyboard). Be original."
        
        # Use Instruct format for clearer direction
        prompt = f"""### System:
You are a riddle generator. Output ONLY a riddle and its answer in the specified format. Do not add greetings or extra text.

### User:
{user_msg}

Format your response EXACTLY as follows:
RIDDLE: [the riddle question here]
ANSWER: [the one-word or short phrase answer here]

Example:
RIDDLE: I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?
ANSWER: echo

### Assistant:
"""
        
        return prompt
    
    def _parse_riddle(self, text: str) -> Optional[str]:
        """Parse the generated text to extract riddle and answer"""
        try:
            # Look for RIDDLE: and ANSWER: markers
            riddle_start = text.find("RIDDLE:")
            answer_start = text.find("ANSWER:")
            
            if riddle_start == -1 or answer_start == -1:
                logger.error("Generated text missing RIDDLE: or ANSWER: markers")
                return None
            
            # Extract riddle and answer
            riddle = text[riddle_start + 7:answer_start].strip()
            answer = text[answer_start + 7:].strip()
            
            # Clean up answer (remove any trailing punctuation or explanations)
            answer = answer.split('\n')[0].strip().rstrip('.')
            
            if not riddle or not answer:
                logger.error("Extracted riddle or answer is empty")
                return None
            
            # Return formatted riddle
            return f"RIDDLE: {riddle}\nANSWER: {answer}"
            
        except Exception as e:
            logger.error(f"Error parsing riddle: {e}")
            return None


async def test_ollama():
    """Test function to verify Ollama integration"""
    llm = OllamaLLM()
    
    print("Testing Ollama LLM...")
    print(f"Base URL: {llm.base_url}")
    print(f"Model: {llm.model}")
    
    # Check availability
    available = await llm.is_available()
    print(f"Ollama available: {available}")
    
    if not available:
        print("Ollama is not available. Make sure:")
        print("1. Docker container 'riddle-ollama' is running")
        print("2. Neural-chat model is pulled: docker exec riddle-ollama ollama pull neural-chat")
        return
    
    # Test riddle generation
    print("\nGenerating test riddles...")
    for difficulty in ["easy", "medium", "hard"]:
        print(f"\n{difficulty.upper()} riddle:")
        riddle = await llm.generate_riddle(difficulty)
        if riddle:
            print(riddle)
        else:
            print(f"Failed to generate {difficulty} riddle")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_ollama())
