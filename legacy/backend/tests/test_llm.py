"""Test the LLM modules (both local and mock) and server LLM import logic."""
import pytest
import sys
from pathlib import Path

# Add backend to path so we can import the modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def test_mock_llm_import():
    """Mock LLM should always import successfully."""
    from mock_llm import LlmChat, UserMessage
    
    msg = UserMessage(text="Create an easy riddle")
    assert hasattr(msg, "text"), "UserMessage should have text attribute"
    
    chat = LlmChat()
    assert hasattr(chat, "send_message"), "LlmChat should have send_message method"

@pytest.mark.asyncio
async def test_mock_llm_generate():
    """Mock LLM should return structured riddle responses."""
    from mock_llm import LlmChat, UserMessage
    
    chat = LlmChat()
    msg = UserMessage(text="Create an easy riddle")
    
    response = await chat.send_message(msg)
    assert "RIDDLE:" in response, "Response should contain RIDDLE: marker"
    assert "ANSWER:" in response, "Response should contain ANSWER: marker"
    
    # Different difficulties should get different responses
    msg_hard = UserMessage(text="Create a hard riddle")
    response_hard = await chat.send_message(msg_hard)
    assert response != response_hard, "Different difficulties should get different riddles"

def test_local_llm_safe_import():
    """Local LLM should import and have required attributes."""
    from llm_local import LlmChat, UserMessage
    
    msg = UserMessage(text="test")
    assert hasattr(msg, "text"), "UserMessage should have text attribute"
    
    chat = LlmChat()
    assert hasattr(chat, "send_message"), "LlmChat should have send_message method"
    assert hasattr(chat, "generator"), "LlmChat should have generator attribute"

@pytest.mark.asyncio
async def test_local_llm_riddle_format():
    """Local LLM should format responses appropriately for riddles."""
    from llm_local import LlmChat, UserMessage
    
    # Use a mock-style prompt that should trigger structured output
    chat = LlmChat()
    msg = UserMessage(text="Create an easy riddle with RIDDLE: and ANSWER: markers")
    
    response = await chat.send_message(msg)
    
    # Either we get a properly formatted response or a fallback
    if "Local model not available" in response or "Failed to generate" in response:
        assert "RIDDLE:" in response, "Fallback should have RIDDLE: marker"
        assert "ANSWER:" in response, "Fallback should have ANSWER: marker"
    else:
        # Real model response should have riddle-like content
        assert len(response) > 20, "Response too short to be valid"
        assert "?" in response, "Response should contain a question mark"

def test_server_llm_import():
    """Server should successfully import an LLM implementation."""
    import importlib
    server = importlib.import_module("server")
    
    # These should exist regardless of which implementation loaded
    assert hasattr(server, "LlmChat"), "Server should import LlmChat"
    assert hasattr(server, "UserMessage"), "Server should import UserMessage"