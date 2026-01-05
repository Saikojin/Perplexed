# Ollama Integration Guide

This document explains how Ollama is integrated into Riddle Master for AI-powered riddle generation.

## Overview

Ollama provides local LLM inference for generating creative riddles. The system uses a fallback chain:

```
Ollama (neural-chat) → Local LLM → Mock LLM
```

If Ollama is unavailable, the system automatically falls back to the next option.

## Architecture

### Components

1. **Ollama Container** (`riddle-ollama`)
   - Runs Ollama service on port 11434
   - Hosts the neural-chat 7B model
   - Optional - system works without it

2. **Backend Integration** (`backend/ollama_llm.py`)
   - Async HTTP client for Ollama API
   - Prompt engineering for riddle generation
   - Response parsing and validation

3. **Fallback Chain** (`backend/server.py`)
   - Primary: Ollama LLM
   - Secondary: Local LLM (Hugging Face transformers)
   - Tertiary: Mock LLM (pre-defined riddles)

## Setup

### Automatic Setup (Recommended)

Run the development script which handles everything:

```batch
.\dev.bat
```

This will:
1. Start Ollama container
2. Pull neural-chat model
3. Configure backend to use Ollama
4. Start all services

### Manual Setup

#### 1. Start Ollama Container

```powershell
# Start Ollama
docker run -d --name riddle-ollama -p 11434:11434 ollama/ollama:latest

# Wait for container to be ready
timeout /t 5

# Pull the neural-chat model
docker exec riddle-ollama ollama pull neural-chat
```

#### 2. Verify Ollama is Running

```powershell
# Check container status
docker ps | findstr ollama

# Test API
curl http://localhost:11434/api/tags
```

Expected response:
```json
{
  "models": [
    {
      "name": "neural-chat:latest",
      "modified_at": "2024-12-09T...",
      "size": 4109865159
    }
  ]
}
```

#### 3. Test Riddle Generation

```powershell
# Activate backend environment
cd backend
call venv\Scripts\activate.bat

# Run test
python ollama_llm.py
```

Expected output:
```
Testing Ollama LLM...
Base URL: http://localhost:11434
Model: neural-chat
Ollama available: True

Generating test riddles...

EASY riddle:
RIDDLE: I have keys but no locks. I have space but no room. You can enter, but you can't go inside. What am I?
ANSWER: keyboard

MEDIUM riddle:
RIDDLE: The more you take, the more you leave behind. What am I?
ANSWER: footsteps
```

## Configuration

### Environment Variables

In `backend/.env`:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=neural-chat
OLLAMA_TIMEOUT=30

# Fallback Configuration
USE_LOCAL_LLM=true
USE_MOCK_LLM=true
```

### Ollama Settings

In `backend/ollama_llm.py`, you can adjust:

```python
# Model parameters
"temperature": 0.8,    # Creativity (0.0-1.0)
"top_p": 0.9,          # Diversity (0.0-1.0)
"max_tokens": 200      # Response length
```

## Usage

### In Backend Code

```python
from ollama_llm import OllamaLLM

# Initialize
llm = OllamaLLM()

# Check availability
if await llm.is_available():
    # Generate riddle
    riddle = await llm.generate_riddle("medium")
    print(riddle)
```

### API Endpoint

The backend automatically uses Ollama when generating riddles:

```bash
# Get daily riddle (uses Ollama if available)
curl -X POST http://localhost:8001/api/riddles/daily \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"difficulty": "medium"}'
```

## Troubleshooting

### Ollama Container Not Starting

**Problem**: `docker run` fails or container exits immediately

**Solutions**:
```powershell
# Check Docker is running
docker ps

# Check logs
docker logs riddle-ollama

# Remove and recreate
docker rm -f riddle-ollama
docker run -d --name riddle-ollama -p 11434:11434 ollama/ollama:latest
```

### Model Not Found

**Problem**: `Ollama available: False` even though container is running

**Solution**:
```powershell
# Pull the model
docker exec riddle-ollama ollama pull neural-chat

# Verify model is available
docker exec riddle-ollama ollama list
```

Expected output:
```
NAME              ID              SIZE      MODIFIED
neural-chat:latest abc123def456   3.8 GB    2 hours ago
```

### Slow Generation

**Problem**: Riddle generation takes 10+ seconds

**Causes**:
1. First request loads model into memory (normal, 5-10 seconds)
2. Insufficient Docker resources
3. CPU-only inference (no GPU)

**Solutions**:
```powershell
# Increase Docker memory (Docker Desktop → Settings → Resources)
# Recommended: 4GB+ RAM, 2+ CPUs

# Check resource usage
docker stats riddle-ollama
```

### Connection Refused

**Problem**: `Connection refused` when calling Ollama API

**Solutions**:
```powershell
# Verify port is exposed
docker port riddle-ollama

# Check if port is in use
netstat -ano | findstr :11434

# Restart container
docker restart riddle-ollama
```

### Timeout Errors

**Problem**: Requests timeout after 30 seconds

**Solutions**:
```python
# Increase timeout in ollama_llm.py
self.timeout = aiohttp.ClientTimeout(total=60)  # 60 seconds
```

## Performance

### Benchmarks

On typical hardware (Intel i5, 8GB RAM):

| Operation | Time | Notes |
|-----------|------|-------|
| First riddle | 8-12s | Model loading |
| Subsequent riddles | 2-5s | Model in memory |
| Model pull | 2-5 min | One-time setup |

### Optimization Tips

1. **Keep container running**: Don't stop/start frequently
2. **Pre-warm model**: Generate a test riddle on startup
3. **Increase resources**: More RAM = faster inference
4. **Use GPU**: If available, configure Ollama to use GPU

## Fallback Behavior

The system gracefully handles Ollama failures:

```python
# Fallback chain in server.py
async def generate_riddle(difficulty: str):
    # Try Ollama
    if ollama_available:
        riddle = await ollama_llm.generate_riddle(difficulty)
        if riddle:
            return riddle
    
    # Try Local LLM
    if local_llm_available:
        riddle = await local_llm.generate_riddle(difficulty)
        if riddle:
            return riddle
    
    # Use Mock LLM
    return mock_llm.generate_riddle(difficulty)
```

### When Fallback Occurs

- Ollama container not running
- Model not pulled
- Network timeout
- Invalid response format
- Any exception during generation

## Advanced Configuration

### Using Different Models

```powershell
# Pull a different model
docker exec riddle-ollama ollama pull llama2

# Update backend/.env
OLLAMA_MODEL=llama2
```

### Custom Prompts

Edit `ollama_llm.py` → `_create_prompt()`:

```python
def _create_prompt(self, difficulty: str) -> str:
    return f"""You are a riddle master. Create a {difficulty} riddle.
    
    Rules:
    - Be creative and original
    - Use wordplay when appropriate
    - Keep answer concise (1-3 words)
    
    Format:
    RIDDLE: [your riddle]
    ANSWER: [the answer]
    """
```

### Monitoring

```powershell
# View Ollama logs in real-time
docker logs riddle-ollama -f

# Check model usage
docker exec riddle-ollama ollama ps

# Monitor resource usage
docker stats riddle-ollama
```

## Security Considerations

1. **Local Only**: Ollama runs locally, no external API calls
2. **No Data Leakage**: Riddles generated locally, not sent to cloud
3. **Resource Limits**: Configure Docker resource limits to prevent abuse
4. **Network Isolation**: Ollama container doesn't need internet access

## References

- [Ollama Documentation](https://ollama.ai/docs)
- [Neural-Chat Model](https://huggingface.co/Intel/neural-chat-7b-v3-1)
- [Docker Ollama Image](https://hub.docker.com/r/ollama/ollama)

---

Last Updated: December 9, 2024
