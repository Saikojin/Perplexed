#!/bin/bash

# Riddle Master - Build and Start Script
# This script uses docker-compose and runs services in background

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════╗
║                                           ║
║         🧩  RIDDLE MASTER  🧩            ║
║                                           ║
║     AI-Powered Daily Puzzle Game         ║
║                                           ║
╚═══════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}✗ $1 is not installed${NC}"
        echo -e "${YELLOW}Install it with: $2${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ $1 found${NC}"
    fi
}

check_command "python3" "sudo apt install python3 (or visit python.org)"
check_command "node" "sudo apt install nodejs (or visit nodejs.org)"
check_command "yarn" "npm install -g yarn"
check_command "docker" "Install Docker from docker.com"
check_command "docker-compose" "Install docker-compose"

# Start Docker containers
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}Starting Docker Containers...${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

# Stop any existing containers
docker-compose down > /dev/null 2>&1 || true

# Start MongoDB and Ollama
docker-compose up -d mongodb ollama
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to start Docker containers${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker containers started${NC}"

# Wait for MongoDB to be ready
echo -e "${YELLOW}Waiting for MongoDB to initialize...${NC}"
sleep 5

# Wait for Ollama to be ready
echo -e "${YELLOW}Waiting for Ollama to initialize...${NC}"
sleep 3

# Pull neural-chat model
echo -e "${YELLOW}Pulling neural-chat model (background)...${NC}"
docker exec riddle-ollama ollama pull neural-chat > /dev/null 2>&1 &

# Backend Setup
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}Setting up Backend...${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

cd "$SCRIPT_DIR/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Backend setup complete${NC}"

# Frontend Setup
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}Setting up Frontend...${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

cd "$SCRIPT_DIR/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing Node dependencies...${NC}"
    yarn install
else
    echo -e "${GREEN}✓ Node modules already installed${NC}"
fi

echo -e "${GREEN}✓ Frontend setup complete${NC}"

# Kill any existing processes on required ports
echo ""
echo -e "${YELLOW}Checking for processes on ports 8001 and 3000...${NC}"

kill_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t > /dev/null 2>&1; then
        echo -e "${YELLOW}Killing process on port $port...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

kill_port 8001
kill_port 3000

# Start Backend
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}Starting Backend Server...${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

cd "$SCRIPT_DIR/backend"
source venv/bin/activate

# Ensure PYTHONPATH points to backend
export PYTHONPATH="$SCRIPT_DIR/backend"

# Start backend in background
nohup uvicorn server:app --host 127.0.0.1 --port 8001 --reload > backend.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}  Logs: tail -f backend/backend.log${NC}"

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8001 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# Start Frontend
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}Starting Frontend Server...${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

cd "$SCRIPT_DIR/frontend"

# Start frontend in background
PORT=3000 BROWSER=none nohup yarn start > frontend.log 2>&1 &
FRONTEND_PID=$!

echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo -e "${BLUE}  Logs: tail -f frontend/frontend.log${NC}"

# Wait for frontend to be ready
echo -e "${YELLOW}Waiting for frontend to compile...${NC}"
sleep 8

# Final output
echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}     🎉  Application Started!  🎉${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}🌐 Frontend:${NC}  http://localhost:3000"
echo -e "${BLUE}🔧 Backend:${NC}   http://localhost:8001"
echo -e "${BLUE}📚 API Docs:${NC}  http://localhost:8001/docs"
echo -e "${BLUE}🐳 Containers:${NC} docker-compose ps"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "   Backend:  tail -f backend/backend.log"
echo -e "   Frontend: tail -f frontend/frontend.log"
echo ""
echo -e "${YELLOW}🛑 Stop:${NC}      docker-compose down && ./stop.sh"
echo ""

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &
elif command -v open &> /dev/null; then
    open http://localhost:3000 &
else
    echo -e "${YELLOW}Please open http://localhost:3000 in your browser${NC}"
fi

echo -e "${GREEN}Services running in background${NC}"
