# Roddle: Standalone Application Plan

This document outlines the strategic plan to convert Roddle from a web-based microservices application into a standalone executable (`.exe`) optimized for desktop distribution, with a forward-looking architecture for future mobile ports.

## Core Philosophy
-   **Self-Contained**: The application must run without requiring the user to install external dependencies like MongoDB or Ollama servers.
-   **Offline Capable**: The core game loop (including riddle generation) should optionally function offline using embedded models.
-   **Portable**: The architecture must prioritize technologies that exist on all major platforms (Windows, macOS, Mobile).

---

## 1. Architecture Changes

We will shift from a **Microservices Architecture** (Frontend + Backend + Database + Inference Server) to a **Monolithic Embedded Architecture**.

| Component | Current State | Planned Standalone State |
| :--- | :--- | :--- |
| **Backend** | FastApi + Uvicorn | FastAPI + Embedded logic |
| **Database** | MongoDB (External Process) | **SQLite** (Embedded File) |
| **LLM Engine** | Ollama (External Service) | **llama-cpp-python** (Embedded Library) |
| **Frontend** | React Dev Server | Static React Build (Served by FastAPI) |
| **Packaging** | Docker / Scripts | PyInstaller (Single `.exe`) |

---

## 2. Key Technology decisions

### A. Database: Migration to SQLite
**Reasoning**: MongoDB requires a separate server process which is heavy and difficult to bundle reliably on consumer hardware. It is also impossible to run a standard Mongo instance on iOS/Android.
**Solution**: 
-   Replace `motor` with `aiosqlite` (async SQLite driver).
-   Store data in a single local file (`roddle.save` or `roddle.db`).
-   Rewrite the database access layer to be SQL-based.
-   **Benefit**: Zero installation, single-file backup, native compatibility with mobile OS.

### B. LLM Engine: Embedded Integration
**Reasoning**: Asking users to "Install Ollama" adds friction. A game should "just work".
**Solution**:
-   Integrate **`llama-cpp-python`** directly into the Python backend.
-   This library binds to C++ implementations of Llama specifically optimized for CPU inference (with GPU acceleration support if detected).
-   **Model Strategy**:
    -   Bundle (or download on first launch) a GGUF format model.
    -   Target "Small & Smart" models (1.5B - 3B parameters) to keep file size reasonable (~1-2GB) and inference fast on consumer CPUs.

### C. Frontend: Static Serving
**Reasoning**: We do not want to require Node.js on the user's machine.
**Solution**:
-   Run `npm run build` to compile the React app into static HTML/CSS/JS.
-   Configure FastAPI to serve these static files as the "GUI" of the application.

---

## 3. Roadmap to Execution

### Phase 1: The Database Migration (Critical Path)
This step is required for both the `.exe` and the future Mobile version.
1.  **Abstract Data Layer**: Create a `DatabaseInterface` class in Python. Move all current MongoDB logic into a `MongoAdapter` implementing this interface.
2.  **Implement SQLite**: Create a `SQLiteAdapter` that implements the same interface.
3.  **Migration Script**: Create a script to transfer data from an existing Mongo instance to the new SQLite file (for development continuity).
4.  **Switch**: Update `server.py` to use the `SQLiteAdapter` by default.

### Phase 2: The Embedded Engine
1.  **Dependency Update**: Add `llama-cpp-python` to requirements.
2.  **Model Selection**: Evaluate candidates for quality vs. size:
    -   *Phi-3 Mini (3.8B)*: High reasoning capability.
    -   *Qwen-2.5-Coder (1.5B)*: Extremely efficient, great at strict formats.
    -   *Gemma 2 (2B)*: Balanced performance.
3.  **Integration**: Create a `LocalLlamaLLM` class for `ModelManager`.
4.  **Prompt Engineering**: Refine system prompts. Smaller models are less forgiving than large ones; prompts must be terse and precise.

### Phase 3: The Build & Packaging
1.  **Build Frontend**: Generate production assets.
2.  **Backend Integration**: Mount static files in `server.py` and ensure API routes are relative (remove `localhost:8000` hardcoding).
3.  **PyInstaller Setup**:
    -   Create `roddle.spec` file.
    -   Configure data analysis to include the `build/` folder.
    -   Configure hidden imports for `uvicorn` and `pydantic`.
    -   Ensure the `.gguf` model file is handled correctly (either bundled or placed alongside the exe).
4.  **Cross-Platform Testing**: Verify the `.exe` works on a clean Windows VM.

---

## 4. Future Mobile Considerations
By completing **Phase 1 (SQLite)** and selecting **GGUF Models (Phase 2)**, the mobile path becomes clear:
-   **Data**: The SQLite database file can be directly used on iOS/Android.
-   **Logic**: The prompt logic remains the same.
-   **Engine**: Mobile apps cannot easily run Python. The Mobile port would likely involve:
    -   *Option A*: React Native / Flutter app using **on-device LLM engines** (like MLC-LLM) executing the *same* converted weights.
    -   *Option B*: A native wrapper around the Python logic (e.g., Kivy/BeeWare), though performance may vary.
-   **Asset Reuse**: The frontend code (React) can be largely reused if wrapped in Capacitor or ported to React Native.
