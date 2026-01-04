# Getting Started with Riddle Master

This guide will get you up and running in minutes.

## 🎯 Choose Your Method

### Method 1: One-Command Start (Recommended)
**Best for:** Quick testing, development, first-time users

```bash
./start.sh
```

**What it does:**
- Checks all prerequisites (Python, Node, MongoDB)
- Sets up backend and frontend automatically
- Starts MongoDB if needed
- Launches both servers
- Generates monthly riddles
- Opens browser to the app
- Creates `stop.sh` for easy shutdown

**Requirements:**
- Python 3.11+
- Node.js 18+
- Yarn
- MongoDB (or Docker)

---

### Method 2: Docker Compose
**Best for:** Isolated environment, production-like testing

```bash
docker-compose up
```

**What it does:**
- Runs everything in containers
- Includes MongoDB automatically
- No local dependencies needed

**Requirements:**
- Docker
- Docker Compose

---

### Method 3: Manual Setup
**Best for:** Development with IDE, debugging

See [README.md](../README.md#manual-setup-advanced) for detailed steps.

---

## 📋 System Requirements

### Minimum
- **OS**: Linux, macOS, or Windows (WSL2)
- **RAM**: 2GB
- **Disk**: 500MB
- **CPU**: 2 cores

### Software
- Python 3.11 or higher
- Node.js 18 or higher
- MongoDB 5.0 or higher (or Docker)
- Yarn package manager

---

## 🚀 First Run

### 1. Start the Application

```bash
cd riddle-master
./start.sh
```

Wait for the browser to open automatically.

### 2. Create Account

1. Click **"Sign up"**
2. Enter username and password
3. Click **"Sign Up"**

### 3. Play Your First Riddle

1. Select a difficulty (**Easy** recommended for first time)
2. Read the riddle
3. Type your answer using the keyboard
4. Press **Enter** to submit
5. See your score!

### 4. Check Leaderboard

Click **"Leaderboard"** to see global rankings and add friends.

---

## 🎮 Daily Usage

### Playing Daily Riddles

- You can play each difficulty level **once per day**
- Come back tomorrow for new riddles
- Build your daily streak!

### Unlocking Premium

- Click the crown icon on "Very Hard" or "Insane"
- Mock payment unlocks harder difficulties
- Get 2-guess and 1-guess challenges

### Adding Friends

1. Go to Leaderboard → Friends tab
2. Enter friend's username
3. Click "Add"
4. See their scores in Friends leaderboard

---

## 🛠️ Troubleshooting

### "Port already in use"

```bash
# Kill processes on ports
lsof -ti:8001 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Then restart
./start.sh
```

### "MongoDB connection failed"

**Option 1: Start MongoDB**
```bash
sudo systemctl start mongodb
# or
mongod
```

**Option 2: Use Docker**
```bash
docker run -d -p 27017:27017 --name mongodb mongo
```

### "Module not found" errors

**Backend:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
yarn install
```

### Backend not starting

Check logs:
```bash
tail -f /tmp/riddle-backend.log
```

Common issues:
- Missing environment variables (check backend/.env)
- MongoDB not running
- Port 8001 in use

### Frontend not loading

Check logs:
```bash
tail -f /tmp/riddle-frontend.log
```

Common issues:
- Backend not responding
- Port 3000 in use
- Node modules not installed

---

## 📱 Platform-Specific Notes

### macOS

```bash
# Install prerequisites with Homebrew
brew install python@3.11 node yarn mongodb-community

# Start MongoDB
brew services start mongodb-community

# Run application
./start.sh
```

### Linux (Ubuntu/Debian)

```bash
# Install prerequisites
sudo apt update
sudo apt install python3.11 python3-pip nodejs npm mongodb

# Install Yarn
npm install -g yarn

# Start MongoDB
sudo systemctl start mongodb

# Run application
./start.sh
```

### Windows (WSL2)

```bash
# Install WSL2 first (Ubuntu recommended)
# Then follow Linux instructions above

# Or use Docker Desktop instead
```

---

## 🔧 Development Tips

### Running in IDE

**VS Code:**
1. Open project folder
2. Press `F5`
3. Select "Full Stack" from dropdown
4. Both backend and frontend start with debugging

**PyCharm:**
1. Open `backend` folder
2. Configure Python interpreter (venv)
3. Create run configuration for uvicorn
4. Run with debugger

### Watching Logs

```bash
# Both servers
tail -f /tmp/riddle-*.log

# Just backend
tail -f /tmp/riddle-backend.log

# Just frontend
tail -f /tmp/riddle-frontend.log
```

### Regenerating Riddles

```bash
curl -X POST http://localhost:8001/api/admin/generate-monthly-riddles
```

### Clearing Database

```bash
mongosh
use riddle_game_db
db.dropDatabase()
```

---

## 📚 Next Steps

- **Customize**: Edit `.env` files for your configuration
- **Build Standalone**: See [docs/STANDALONE_BUILD.md](STANDALONE_BUILD.md)
- **Deploy**: See [README.md](../README.md#production-deployment)
- **Contribute**: Check GitHub Issues for tasks

---

## 🆘 Getting Help

- **Documentation**: Check [README.md](../README.md) and [docs/](.)
- **API Docs**: http://localhost:8001/docs (when running)
- **GitHub Issues**: Report bugs and request features
- **Logs**: Check `/tmp/riddle-*.log` for errors

---

## ✅ Quick Checklist

Before asking for help, verify:

- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Yarn installed (`yarn --version`)
- [ ] MongoDB running (`mongosh` connects)
- [ ] Ports 8001 and 3000 are free
- [ ] `.env` files exist in backend and frontend
- [ ] No errors in logs (`tail -f /tmp/riddle-*.log`)
- [ ] Internet connection (for AI riddle generation)

---

Happy riddling! 🧩
