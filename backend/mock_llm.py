"""
Lightweight fallback LLM interface used in development.

This module implements the same public API the server expects: `UserMessage`
and `LlmChat` with an async `send_message(...)` method. It returns static
responses and is used when no local model is available.
"""

class UserMessage:
    def __init__(self, text: str):
        # server constructs UserMessage(text=...)
        self.text = text


class LlmChat:
    async def send_message(self, user_message: UserMessage, **kwargs):
        """Return a simple placeholder response so the app can run offline."""
        prompt = getattr(user_message, "text", "")
        # Keep response structured similar to the LLM output the server expects
        # (server looks for 'RIDDLE:' and 'ANSWER:')
        if not prompt:
            return "RIDDLE: A riddle is missing its prompt. ANSWER: UNKNOWN"

        # Very small deterministic generation based on prompt length to be predictable
        if "easy" in prompt.lower():
            return "RIDDLE: I have keys but open no locks. I have space but no room. You can enter but can't go inside. What am I? ANSWER: KEYBOARD"
        elif "medium" in prompt.lower():
            return "RIDDLE: The more you take, the more you leave behind. What am I? ANSWER: FOOTSTEPS"
        elif "hard" in prompt.lower():
            return "RIDDLE: I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I? ANSWER: ECHO"
        else:
            return "RIDDLE: I am the thing that always runs but never walks. I have a bed but never sleep. What am I? ANSWER: RIVER"
