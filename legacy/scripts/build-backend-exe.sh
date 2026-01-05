#!/bin/bash

# Build Standalone Backend Executable

set -e

echo "Building Riddle Master Backend Executable..."

# Navigate to backend
cd "$(dirname "$0")/../backend"

# Activate virtual environment
if [ -d "venv" ]; then
  source venv/bin/activate
else
  echo "Error: Virtual environment not found. Run setup first."
  exit 1
fi

# Install PyInstaller
if ! pip show pyinstaller > /dev/null 2>&1; then
  echo "Installing PyInstaller..."
  pip install pyinstaller
fi

# Create spec file if it doesn't exist
if [ ! -f "riddle-backend.spec" ]; then
  echo "Creating PyInstaller spec file..."
  pyi-makespec --onefile --name riddle-backend server.py
fi

# Build executable
echo "Building executable..."
pyinstaller riddle-backend.spec --clean

echo "✅ Backend executable built successfully!"
echo "📦 Output: backend/dist/riddle-backend"
echo ""
echo "To run: ./backend/dist/riddle-backend"
echo "Note: Requires MongoDB running on localhost:27017"