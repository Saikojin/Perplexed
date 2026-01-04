#!/bin/bash

# Complete Local Setup Script

set -e

echo "🎮 Riddle Master - Local Setup"
echo "================================"

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v yarn >/dev/null 2>&1 || { echo "❌ Yarn is required but not installed."; exit 1; }
command -v mongod >/dev/null 2>&1 || { echo "⚠️  MongoDB not found. Please install MongoDB."; }

echo "✅ Prerequisites check passed"

# Backend setup
echo ""
echo "📦 Setting up Backend..."
cd "$(dirname "$0")/../backend"

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Backend setup complete"

# Frontend setup
echo ""
echo "📦 Setting up Frontend..."
cd ../frontend

echo "Installing Node dependencies..."
yarn install

echo "✅ Frontend setup complete"

# MongoDB check
echo ""
if pgrep mongod > /dev/null; then
  echo "✅ MongoDB is running"
else
  echo "⚠️  MongoDB is not running. Start it with: mongod"
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Generate monthly riddles:"
echo "   cd backend && source venv/bin/activate"
echo "   uvicorn server:app --host 0.0.0.0 --port 8001 --reload &"
echo "   curl -X POST http://localhost:8001/api/admin/generate-monthly-riddles"
echo ""
echo "2. Run the application:"
echo "   Terminal 1: cd backend && source venv/bin/activate && uvicorn server:app --reload"
echo "   Terminal 2: cd frontend && yarn start"
echo ""
echo "3. Open http://localhost:3000"