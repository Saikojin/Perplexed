# Perplexed

A simplified, standalone version of the Roddle Riddle Game.

## Features
- **Zero Dependencies**: Uses SQLite instead of MongoDB.
- **Embedded AI**: Uses `llama-cpp-python` for local inference (or Mock mode if no model found).
- **Single Process**: Backend serves the API and Static frontend files.

## Directory Structure
- `backend/`: FastAPI application + SQLite + LLM logic.
- `frontend/`: React source code.


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

## Compilation Steps

To compile the project into a standalone `.exe` (Windows) for distribution:

1.  **Prerequisites**:
    Ensure you have the backend virtual environment active and dependencies installed:
    ```bash
    .\run.bat
    # (Ctrl+C to stop the server, but keep the env ready or activate it manually)
    ```

2.  **Install Build Tools**:
    ```bash
    pip install pyinstaller
    ```

3.  **Frontend Build**:
    Compile the React frontend into static assets:
    ```bash
    cd frontend
    npm run build
    ```
    *Note: The build output will be automatically picked up if `backend/static` is configured correctly, or ensure the build artifacts are moved to `backend/static`.*

4.  **Run Build Script**:
    Use the provided PyInstaller spec file to bundle everything:
    ```bash
    pyinstaller build.spec --clean --noconfirm
    ```

5.  **Output**:
    -   **Folder**: `dist/Perplexed/` (Contains the uncompressed executable and dependencies)
    -   **Executable**: `dist/Perplexed/Perplexed.exe`
    -   **Zip**: `dist/Perplexed.zip` (If you manually zip it or have a script for it)

    **Important**: Do not use the `build/` folder; it contains temporary compilation files.


