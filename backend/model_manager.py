import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from fastapi import HTTPException
from ollama_llm import OllamaLLM
from ollama_llm import OllamaLLM
from mock_llm import LlmChat as MockLlmChat
from llm_online import OpenAIService, AnthropicService

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages LLM interactions, including model selection, fallback, and downloading.
    """
    def __init__(self, ollama_url: str = "http://127.0.0.1:11434", default_model: str = "neural-chat"):
        self.ollama = OllamaLLM(base_url=ollama_url, model=default_model)
        self.mock = MockLlmChat()
        self.openai = OpenAIService()
        self.anthropic = AnthropicService()
        self.default_model = default_model
        
        # Define prompts here
        self.difficulty_prompts = {
            "easy": "Create a very easy riddle for children. The answer must be a single common word (3-6 letters). Make it simple and fun.",
            "medium": "Create a medium difficulty riddle. The answer must be a single word (4-8 letters). Make it clever but not too hard.",
            "hard": "Create a challenging riddle. The answer must be a single word (5-10 letters). Make it require creative thinking.",
            "very_hard": "Create a very difficult riddle. The answer must be a single uncommon word (6-12 letters). Make it cryptic and complex.",
            "insane": "Create an extremely difficult, mind-bending riddle. The answer must be a single word (7-15 letters). Make it require deep lateral thinking."
        }
        
        self.theme_prompts = {
            "default": "",
            "cyberpunk": "Style: Cyberpunk. Use high-tech, neon, dystopian, or hacking related metaphors. The answer should still be a regular word, but the riddle phrasing should feel futuristic and gritty.",
            "fantasy": "Style: High Fantasy. Use archaic language, mention magic, dragons, dungeons, or medieval elements. The riddle should feel like it was found in an ancient scroll.",
            "horror": "Style: Horror. Use spooky, eerie, and dark language. The riddle should be unsettling and mysterious (but acceptable for a general audience).",
            "scifi": "Style: Sci-Fi. Use space, alien, physics, or cosmic metaphors.",
            "noir": "Style: Film Noir. Write it like a 1940s detective narrating a mystery. Gritty, rain-soaked, and cynical."
        }

    async def get_available_models(self) -> List[Dict]:
        """Get list of available models from Ollama"""
        return await self.ollama.list_models()

    async def pull_model(self, model_name: str) -> bool:
        """Trigger Ollama to pull a model"""
        return await self.ollama.pull_model(model_name)

    async def generate_riddle(self, difficulty: str, theme: str = "default", preferred_model: str = None, api_keys: Dict[str, str] = {}) -> Tuple[str, str]:
        """
        Generate a riddle using the specified configuration.
        """
        # Determine prompt
        base_prompt = self.difficulty_prompts.get(difficulty, self.difficulty_prompts["medium"])
        theme_instruction = self.theme_prompts.get(theme, "")
        
        # Instruction for Ollama (System/User format handled in OllamaLLM)
        full_instruction = f"{base_prompt} {theme_instruction}"
        
        # Prompt for Online LLMs (Need strict formatting instructions)
        formatting_instruction = "You are a riddle generator. Output ONLY a riddle and its answer. Format EXACTLY as: RIDDLE: [riddle text] ANSWER: [one word answer]."
        online_prompt = f"{formatting_instruction} {full_instruction}"
        
        logger.info(f"Generated Prompt: {full_instruction}")
        
        # Configure model
        target_model = preferred_model if preferred_model else self.default_model
        
        try:
            riddle_text = None
            
            # OpenAI
            if target_model.startswith("gpt-"):
                api_key = api_keys.get("openai")
                if not api_key:
                    raise HTTPException(status_code=400, detail=f"OpenAI API Key required for model {target_model}")
                logger.info(f"Using OpenAI model: {target_model}")
                riddle_text = await self.openai.generate_completion(api_key, target_model, online_prompt)
                
            # Anthropic
            elif target_model.startswith("claude-"):
                api_key = api_keys.get("anthropic")
                if not api_key:
                    raise HTTPException(status_code=400, detail=f"Anthropic API Key required for model {target_model}")
                logger.info(f"Using Anthropic model: {target_model}")
                riddle_text = await self.anthropic.generate_completion(api_key, target_model, online_prompt)
            
            # Ollama (Default)
            else:
                original_model = self.ollama.model
                # Check if we need to switch model temporarily
                if target_model != original_model:
                     logger.info(f"Switching model to {target_model} (default: {original_model})")
                     self.ollama.model = target_model
                     
                try:
                    # Check availability
                    is_available = await self.ollama.is_available()
                    if not is_available:
                        logger.warning("Ollama not available")
                        
                    logger.info(f"Attempts generation with {self.ollama.model}...")
                    riddle_text = await self.ollama.generate_riddle(difficulty, instruction=full_instruction)
                finally:
                    # Restore default model if changed
                    if target_model != original_model:
                        self.ollama.model = original_model
            
            if riddle_text:
                # Parse
                parts = riddle_text.split("ANSWER:")
                if len(parts) < 2:
                    logger.error(f"Failed to parse riddle response: {riddle_text}")
                    # Try soft parse?
                    raise ValueError(f"Invalid format from LLM: {riddle_text}")
                    
                riddle = parts[0].replace("RIDDLE:", "").strip()
                answer = parts[1].strip().upper()
                answer = answer.split()[0] if answer else "UNKNOWN" # Take first word
                
                return riddle, answer
            else:
                raise ValueError("LLM returned None")

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")

