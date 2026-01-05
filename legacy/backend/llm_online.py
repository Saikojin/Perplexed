import aiohttp
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.base_url = "https://api.openai.com/v1"

    async def generate_completion(self, api_key: str, model: str, prompt: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API Error ({response.status}): {error_text}")
                        return None
                    
                    data = await response.json()
                    return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenAI Connection Error: {e}")
            return None

class AnthropicService:
    def __init__(self):
        self.base_url = "https://api.anthropic.com/v1"

    async def generate_completion(self, api_key: str, model: str, prompt: str) -> Optional[str]:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.8
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/messages", headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Anthropic API Error ({response.status}): {error_text}")
                        return None
                    
                    data = await response.json()
                    return data['content'][0]['text']
        except Exception as e:
            logger.error(f"Anthropic Connection Error: {e}")
            return None
