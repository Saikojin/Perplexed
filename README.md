# Perplexed

A simplified, standalone version of the Roddle Riddle Game.

## Features
- **Zero Dependencies**: Uses SQLite instead of MongoDB.
- **Embedded AI**: Uses `llama-cpp-python` for local inference (or Mock mode if no model found).
- **Single Process**: Backend serves the API and Static frontend files.

## Directory Structure
- `backend/`: FastAPI application + SQLite + LLM logic.
- `frontend/`: React source code.
- `legacy/`: Complete backup of the original microservices-based project (Docker, Mongo, Ollama).

## How to Run

1. **Run the Backend**
   Double-click `run.bat` or run:
   ```bash
   .\run.bat
   ```
   This will:
   - Create a python venv.
   - Install dependencies (`fastapi`, `aiosqlite`, etc).
   - Start the server on `http://localhost:8000`.

2. **Frontend Development**
   Open a new terminal:
   ```bash
   cd frontend
   npm install
   npm start
   ```
   Access at `http://localhost:3000`.

3. **Default Model**
   The default model should be `tinyllama`, however github has a size limit of 100MB.
   The game will use a fallback of fixed riddles without the model. You must go to settings and add the model URL to use it.
   ```
   https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
   ```
 
## Building for Production (Standalone .exe compatibility)

The goal is to bundle this into a single executable.
1. Build frontend: `cd frontend && npm run build`
2. Move content of `frontend/build` to `backend/static`.
3. Use PyInstaller on `backend/main.py`.

## Legacy Project
The original project files are preserved in the `legacy/` folder for reference.

## Secret Sauce (LLM Logic)
The core logic for riddle generation is contained in `backend/llm.py`. 
**This file is NOT included in the repository** as it contains the proprietary "Secret Sauce" of the project.

To run the project, you must create your own `backend/llm.py`. A basic class structure should look like this:

```python
class LLMEngine:
    def __init__(self):
        # Initialize your model
        pass

    def generate_riddle(self, difficulty="medium", topic=None):
        # Return a dictionary with 'riddle' and 'answer'
        return {"riddle": "Example riddle", "answer": "example"}
```
