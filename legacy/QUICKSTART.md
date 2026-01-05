# Quick Start Guide

## 🚀 Fastest Way to Run (ONE COMMAND!)

```bash
git clone <repo-url>
cd riddle-master
./start.sh
```

**That's it!** The browser will open automatically to http://localhost:3000

The script handles everything:
- ✅ Prerequisites check
- ✅ Backend setup (Python venv, dependencies)
- ✅ Frontend setup (Yarn install)
- ✅ MongoDB start (or Docker)
- ✅ Server start (both backend & frontend)
- ✅ Monthly riddles generation
- ✅ Browser launch

### Stop the App
```bash
./stop.sh
# Or press Ctrl+C and choose "Stop servers and exit"
```

---

## 🐳 Using Docker (Alternative)

```bash
# Clone and start everything
git clone <repo-url>
cd riddle-master
docker-compose up

# Generate monthly riddles (in another terminal)
docker exec riddle-backend curl -X POST http://localhost:8001/api/admin/generate-monthly-riddles

# Open http://localhost:3000
```

---

## 🎮 First Time Usage

1. **Register Account**: Click "Sign up" and create account
2. **Play Daily Riddle**: Select a difficulty (Easy/Medium/Hard)
3. **Type Answer**: Use keyboard to fill tiles
4. **Unlock Premium**: Click crown icon for Very Hard & Insane
5. **Check Leaderboard**: See rankings and add friends

## 📦 Building Standalone

### Desktop App (Electron)
```bash
./scripts/build-electron.sh
# Output: frontend/dist/Riddle Master.exe (or .app, .AppImage)
```

### Backend Executable
```bash
./scripts/build-backend-exe.sh
# Output: backend/dist/riddle-backend
```

## 🤖 LLM Configuration

The backend can use either a local AI model or mock responses for riddle generation:

### Option 1: Local Model (Offline Capable)
```bash
# Install with local model support (larger download)
cd backend
pip install -r requirements.txt

# Or minimal install (mock responses only)
pip install -r requirements.txt --exclude torch transformers

# Control via environment:
export LLM_MODE=local  # use local model if available
export LLM_MODE=mock   # always use mock responses
```

**Model Options:**
- Default: `distilgpt2` (small, fast, ~500MB)
- Better quality: Install `gpt2-medium` or `gpt2-large`
- Tiny offline: Use `TinyLlama` or similar

The local model will download on first use. Mock responses are always available as fallback.

## 🐛 Common Issues

**Port 8001 in use:**
```bash
lsof -ti:8001 | xargs kill -9
```

**MongoDB not running:**
```bash
# Start MongoDB
mongod --dbpath /path/to/data

# Or with Docker
docker run -d -p 27017:27017 mongo
```

**Missing dependencies:**
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && yarn install
```

## 📚 More Info

- Full docs: [README.md](README.md)
- API docs: http://localhost:8001/docs
- Tech support: GitHub Issues