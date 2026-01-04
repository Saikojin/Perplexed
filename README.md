# Riddle Master - AI-Powered Daily Puzzle Game

A Wordle-style riddle game with AI-generated puzzles, daily challenges, and multiplayer leaderboards.

## ✨ Features

- 🧩 **Daily Riddles**: One unique riddle per day for each difficulty level
- 🤖 **AI-Generated**: Riddles created by Ollama (neural-chat model) or fallback to local/mock LLM
- 🎯 **5 Difficulty Levels**: Easy to Insane with varying guess counts (2-5 guesses)
- 🏆 **Leaderboards**: Global and friends rankings
- 🔒 **Encrypted Storage**: Riddles and answers securely encrypted in MongoDB
- 💎 **Premium Tiers**: Unlock Very Hard and Insane difficulties
- ⚡ **Offline-Ready**: Monthly bulk generation for offline play
- 👥 **Multi-User Support**: Multiple users can play simultaneously with their own riddles
- 📊 **Comprehensive Logging**: Timestamped logs for debugging and monitoring
- 🔄 **Auto-Restart**: Development environment with hot reload

## 🛠️ Tech Stack

- **Frontend**: React 18, Tailwind CSS, shadcn/ui, React Router
- **Backend**: FastAPI (Python 3.13), Motor (async MongoDB)
- **Database**: MongoDB 5.0+ (Docker)
- **AI**: Ollama (neural-chat 7B) with fallback chain (Ollama → Local LLM → Mock)
- **Deployment**: Docker Compose for services, local dev with `dev.bat`
- **Security**: JWT authentication, Fernet encryption, bcrypt password hashing

## 📋 Prerequisites

- **Python 3.11+** (3.13 recommended)
- **Node.js 18+** and **Yarn 1.22+**
- **Docker Desktop** (for MongoDB and Ollama)
- **Windows 10/11** (for `dev.bat` script) or WSL/Linux (for `start.sh`)

## 🚀 Quick Start

### Windows Development (Recommended)

```batch
# 1. Ensure Docker Desktop is running

# 2. Clone the repository
git clone <your-repo-url>
cd Roddle

# 3. Start all services (MongoDB, Ollama, Backend, Frontend)
.\dev.bat
```

The `dev.bat` script will:
- ✅ Check Docker is running
- ✅ Start MongoDB and Ollama containers
- ✅ Setup Python virtual environment
- ✅ Install backend dependencies
- ✅ Start backend server with timestamp logging
- ✅ Install frontend dependencies  
- ✅ Start frontend dev server with timestamp logging
- ✅ Open separate windows for backend and frontend

**Access the app:** http://localhost:3000  
**API Docs:** http://localhost:8001/docs  
**Backend Logs:** `backend\backend.log` (with timestamps)  
**Frontend Logs:** `frontend\frontend.log` (with timestamps)

**Stop servers:** Close the backend/frontend windows or press Ctrl+C

### Linux/Mac Development

```bash
# Start everything with one command
./start.sh

## Manual Setup (Advanced)

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd riddle-master
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configuration is already in .env file
# Update if needed: EMERGENT_LLM_KEY, JWT_SECRET_KEY, ENCRYPTION_KEY
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
yarn install

# .env already configured
```

### 4. Database Setup

```bash
# Start MongoDB (if not running)
mongod --dbpath /path/to/data/db

# Or using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 5. Generate Monthly Riddles

```bash
# Start backend first
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# In another terminal, generate riddles
curl -X POST http://localhost:8001/api/admin/generate-monthly-riddles
```

### 6. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn start
```

**Access the app:** http://localhost:3000

---

## 🎮 Usage

### First Time
1. Run `./start.sh`
2. Wait for browser to open
3. Register an account
4. Play your first riddle!

### Daily Play
- Each difficulty can be played once per day
- Come back tomorrow for new riddles
- Track progress on leaderboard

### Stop/Restart
```bash
./stop.sh           # Stop servers
./start.sh          # Start again
```

---

## IDE Setup

### VS Code

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["server:app", "--reload", "--host", "0.0.0.0", "--port", "8001"],
      "cwd": "${workspaceFolder}/backend"
    },
    {
      "name": "Frontend: React",
      "type": "node",
      "request": "launch",
      "cwd": "${workspaceFolder}/frontend",
      "runtimeExecutable": "yarn",
      "runtimeArgs": ["start"]
    }
  ]
}
```

### PyCharm

1. Open `backend` folder as project
2. Configure Python interpreter: Settings → Project → Python Interpreter → Add → Existing → `backend/venv`
3. Run configuration:
   - Module: `uvicorn`
   - Parameters: `server:app --reload`
   - Working directory: `backend`

## Building Standalone Application

### Option 1: Docker (Recommended)

```bash
# See docker-compose.yml
docker-compose up --build

# Access at http://localhost:3000
```

### Option 2: Desktop App with Electron

```bash
cd scripts
./build-electron.sh

# Outputs to frontend/dist/
```

### Option 3: Python Executable

```bash
cd scripts
./build-backend-exe.sh

# Outputs to backend/dist/
```

## Project Structure

```
riddle-master/
├── backend/
│   ├── server.py           # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Backend configuration
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── pages/         # Page components
│   │   └── components/    # Reusable components
│   ├── package.json       # Node dependencies
│   └── .env              # Frontend configuration
├── scripts/               # Build scripts
├── docs/                  # Additional documentation
└── README.md             # This file
```

## API Documentation

Once backend is running, visit: http://localhost:8001/docs

## 📊 Logging & Debugging

### Timestamped Logs

All logs include timestamps for easier debugging:

**Backend logs** (`backend/backend.log`):
```
[2024-12-09 16:58:00] 2024-12-09 16:58:00 - __main__ - INFO - MongoDB connection successful
[2024-12-09 16:58:01] INFO: Application startup complete.
[2024-12-09 16:58:05] 2024-12-09 16:58:05 - __main__ - INFO - Login attempt for username: testuser
```

**Frontend logs** (`frontend/frontend.log`):
```
[2024-12-09 16:58:10] yarn run v1.22.22
[2024-12-09 16:58:15] Compiled successfully!
```

**Browser console logs** (F12 → Console):
```javascript
[2024-12-09T23:58:20.123Z] Making request to: http://localhost:8001/api/auth/login
[2024-12-09T23:58:20.456Z] Riddle generated: {riddleId: "abc123"}
```

### Viewing Logs

```powershell
# View backend logs
type backend\backend.log

# Tail backend logs in real-time
Get-Content backend\backend.log -Wait -Tail 50

# View frontend logs
type frontend\frontend.log

# Tail frontend logs in real-time
Get-Content frontend\frontend.log -Wait -Tail 50
```

### Debugging Tips

1. **Check backend health**: http://localhost:8001/api/health
2. **Monitor MongoDB**: `docker logs riddle-mongodb -f`
3. **Monitor Ollama**: `docker logs riddle-ollama -f`
4. **Browser DevTools**: F12 → Console tab for frontend logs
5. **Check timestamps**: Compare log timestamps to track event sequences

## 🔧 Troubleshooting

### Docker Issues

**Docker not running:**
```powershell
# Start Docker Desktop manually
# Then verify:
docker ps
```

**MongoDB connection failed:**
```powershell
# Check if MongoDB is running
docker ps | findstr mongo

# Restart MongoDB
docker restart riddle-mongodb

# Test connection
docker exec riddle-mongodb mongosh --eval "db.adminCommand('ping')"
# Should return: { ok: 1 }
```

**Ollama not responding:**
```powershell
# Check Ollama status
docker ps | findstr ollama

# View Ollama logs
docker logs riddle-ollama -f

# Restart Ollama
docker restart riddle-ollama
```

### Port Conflicts

**Port 8001 (Backend) already in use:**
```powershell
# Find process using port 8001
netstat -ano | findstr :8001

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Port 3000 (Frontend) already in use:**
```powershell
# Find process using port 3000
netstat -ano | findstr :3000

# Kill the process
taskkill /PID <PID> /F
```

### Backend Won't Start

**"System cannot find the path specified":**
- Make sure you're running `dev.bat` from the project root directory
- Check that `backend/venv` exists
- Try deleting `backend/venv` and running `dev.bat` again

**MongoDB connection timeout:**
```powershell
# Ensure MongoDB is running
docker ps

# If not running, start it
docker-compose up -d mongodb

# Wait 5 seconds, then restart backend
```

### Frontend Issues

**"Module not found" errors:**
```bash
cd frontend
rm -rf node_modules yarn.lock
yarn install
```

**Build errors:**
```bash
cd frontend
yarn cache clean
yarn install
```

### Login/Authentication Issues

1. **Check backend is running**: http://localhost:8001/docs
2. **Check MongoDB has data**:
   ```powershell
   docker exec riddle-mongodb mongosh roddle --eval "db.users.countDocuments()"
   ```
3. **Check browser console** (F12) for error messages
4. **Check backend logs** for authentication errors
5. **Try registering a new user** instead of logging in

### Riddle Generation Issues

**Riddles not generating:**
1. Check Ollama is running: `docker ps | findstr ollama`
2. Check Ollama logs: `docker logs riddle-ollama -f`
3. Backend will fall back to mock riddles if Ollama fails
4. Check backend logs for generation errors

**Slow riddle generation:**
- First riddle generation may take 5-10 seconds (model loading)
- Subsequent riddles should be faster (2-5 seconds)
- If consistently slow, check Ollama container resources

### Getting Help

1. Check `context.txt` for recent changes and known issues
2. Check `LOGGING_INVESTIGATION.md` for debugging guides
3. Check `BACKEND_STARTUP_FIX.md` for startup issues
4. Review logs with timestamps to identify when issues occur

## 📚 Additional Documentation

- `context.txt` - Development context and recent changes
- `LOGGING_INVESTIGATION.md` - Logging and debugging guide
- `BACKEND_STARTUP_FIX.md` - Backend startup troubleshooting
- `LOGGING_FIX_SUMMARY.md` - Logging script fixes
- `docs/OLLAMA_SETUP.md` - Ollama integration details

## License

MIT License - See LICENSE file for details
