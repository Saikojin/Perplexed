@echo off
setlocal enabledelayedexpansion

:: Riddle Master - Development Script for Windows
:: This script uses docker-compose and opens terminals for backend/frontend logs
set "OLLAMA_MODEL=neural-chat"

echo.
echo ╔═══════════════════════════════════════════╗
echo ║                                           ║
echo ║         🧩  RIDDLE MASTER  🧩            ║
echo ║                                           ║
echo ║     AI-Powered Daily Puzzle Game          ║
echo ║                                           ║
echo ╚═══════════════════════════════════════════╝
echo.

:: Check prerequisites
echo Checking prerequisites...

:: Check Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Python is not installed
    echo Please install Python from python.org
    exit /b 1
) else (
    echo ✓ Python found
)

:: Check Docker
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Docker is not running or not installed
    echo Please start Docker Desktop or install it from docker.com
    exit /b 1
) else (
    echo ✓ Docker found
)

:: Check Node.js
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Node.js is not installed
    echo Please install Node.js from nodejs.org
    exit /b 1
) else (
    echo ✓ Node.js found
)

:: Check Yarn
where yarn > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Yarn is not installed
    echo Attempting to install Yarn globally...
    call npm install -g yarn
    if %errorlevel% neq 0 (
        echo ✗ Failed to install Yarn
        echo Please run 'npm install -g yarn' manually and re-run this script
        exit /b 1
    ) else (
        echo ✓ Yarn installed successfully
    )
) else (
    echo ✓ Yarn found
)

echo.
echo ═══════════════════════════════════════
echo Starting Docker Containers...
echo ═══════════════════════════════════════

:: Stop any existing containers
echo Stopping existing containers...
docker-compose down > nul 2>&1

:: Start containers with docker-compose
echo Starting MongoDB and Ollama containers...
docker-compose up -d mongodb ollama
if %errorlevel% neq 0 (
    echo ✗ Failed to start containers
    exit /b 1
)
echo ✓ Containers started

:: Wait for MongoDB to be ready
echo Waiting for MongoDB to initialize...
timeout /t 5 /nobreak > nul

:: Wait for Ollama to be ready
echo Waiting for Ollama to initialize...
timeout /t 30 /nobreak > nul

:: Pull neural-chat model
echo Pulling %OLLAMA_MODEL% model (this may take a few minutes on first run)...
docker exec riddle-ollama ollama pull %OLLAMA_MODEL% > nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ %OLLAMA_MODEL% model ready
) else (
    echo ! Model pull in progress (will continue in background)
    start /B docker exec riddle-ollama ollama pull %OLLAMA_MODEL% > nul 2>&1
)

echo.
echo ═══════════════════════════════════════
echo Setting up Backend...
echo ═══════════════════════════════════════

cd backend

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ✗ Failed to create virtual environment
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ✗ Failed to activate virtual environment
    exit /b 1
)

:: Install dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip > nul 2>&1
pip install -r requirements.txt > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Failed to install Python dependencies
    exit /b 1
)

echo ✓ Backend setup complete

:: Check Ollama Connectivity
echo.
echo ═══════════════════════════════════════
echo Checking Ollama Connectivity...
echo ═══════════════════════════════════════
call venv\Scripts\activate.bat
python ..\test_ollama_debug.py
if %errorlevel% neq 0 (
    echo ! Ollama connectivity check failed.
    echo ! Please check if the Docker container is running and port 11434 is exposed.
    pause
) else (
    echo ✓ Ollama connectivity verified.
)

:: Save backend directory for later use
set "BACKEND_DIR=%CD%"

echo.
echo ═══════════════════════════════════════
echo Setting up Frontend...
echo ═══════════════════════════════════════

cd ..\frontend

:: Install Node dependencies if needed
if not exist node_modules (
    echo Installing Node dependencies...
    call yarn install
    if %errorlevel% neq 0 (
        echo ✗ Failed to install Node dependencies
        exit /b 1
    )
) else (
    echo ✓ Node modules already installed
)

echo ✓ Frontend setup complete

:: Save frontend directory for later use
set "FRONTEND_DIR=%CD%"

:: Kill processes on ports if needed
echo.
echo Checking for processes on ports 8001 and 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /F /PID %%a >nul 2>&1

echo.
echo ═══════════════════════════════════════
echo Starting Servers...
echo ═══════════════════════════════════════

:: Start Backend in new terminal with logging
echo Starting backend server...
start "Roddle Backend" cmd /k "set OLLAMA_MODEL=%OLLAMA_MODEL%&& "%BACKEND_DIR%\start-backend-with-log.bat" "%BACKEND_DIR%""

:: Start Frontend in new terminal with logging
echo Starting frontend server...
start "Roddle Frontend" cmd /k ""%FRONTEND_DIR%\start-frontend-with-log.bat" "%FRONTEND_DIR%""

:: Wait for services to start
echo.
echo Waiting for services to initialize...
timeout /t 8 /nobreak > nul

:: Check if services are running
echo.
echo Checking service status...

netstat -ano | findstr ":8001" > nul
if %errorlevel% equ 0 (
    echo ✓ Backend running on http://localhost:8001
) else (
    echo ! Backend may not have started. Check the "Roddle Backend" window for errors.
)

netstat -ano | findstr ":3000" > nul
if %errorlevel% equ 0 (
    echo ✓ Frontend running on http://localhost:3000
) else (
    echo ! Frontend may not have started. Check the "Roddle Frontend" window for errors.
)

echo.
echo ═══════════════════════════════════════
echo ✓ All services started!
echo ═══════════════════════════════════════
echo.
echo 📱 Frontend: http://localhost:3000
echo 🔧 Backend API: http://localhost:8001/docs
echo � Docker Containers: docker-compose ps
echo.
echo Terminal Windows:
echo   - "Roddle Backend" - Backend server logs
echo   - "Roddle Frontend" - Frontend dev server logs
echo.
echo To stop services:
echo   - Close the backend/frontend terminal windows
echo   - Run: docker-compose down
echo   - Or run: .\stop.bat
echo.

echo.
echo Opening browser...
start http://localhost:3000

echo.
echo Press any key to stop all services...
pause > nul

echo.
echo Stopping services...
taskkill /F /IM python.exe > nul 2>&1
taskkill /F /IM node.exe > nul 2>&1
docker-compose down
echo Done.
