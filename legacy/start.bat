@echo off
setlocal enabledelayedexpansion

:: Riddle Master - Startup Script for Windows (Background Mode)
:: This script replicates dev.bat checks but runs everything in the background 
:: and opens the browser for a seamless experience.

set "STATUS_OK=[OK] "
set "STATUS_INFO=[INFO] "
set "STATUS_ERROR=[ERROR] "
set "CHECK_MARK=+"
set "CROSS_MARK=x"
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
echo %STATUS_INFO%STEP: starting prerequisite checks

:: Check Python
echo STEP: checking Python installation...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Python is not installed
    echo Please install Python from python.org
    exit /b 1
) else (
    echo ✓ Python found
)

:: Check Docker
echo STEP: checking Docker...
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Docker is not running or not installed
    echo Please start Docker Desktop or install it from docker.com
    exit /b 1
) else (
    echo ✓ Docker found
)

:: Check Node.js
echo STEP: checking Node.js...
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Node.js is not installed
    echo Please install Node.js from nodejs.org
    exit /b 1
) else (
    echo ✓ Node.js found
)

:: Check Yarn
echo %STATUS_INFO%STEP: checking Yarn...
where yarn > nul 2>&1
if %errorlevel% neq 0 (
    echo %STATUS_ERROR%%CROSS_MARK% Yarn is not installed
    echo %STATUS_INFO%Attempting to install Yarn globally...
    call npm install -g yarn
    if %errorlevel% neq 0 (
        echo %STATUS_ERROR%%CROSS_MARK% Failed to install Yarn
        echo %STATUS_INFO%Please run 'npm install -g yarn' manually and re-run this script
        exit /b 1
    ) else (
        echo %STATUS_OK%%CHECK_MARK% Yarn installed successfully
    )
) else (
    echo %STATUS_OK%%CHECK_MARK% Yarn found
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

:: Pull model
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

:: Check Ollama Connectivity (EXACT MATCH of dev.bat)
echo.
echo ═══════════════════════════════════════
echo Checking Ollama Connectivity...
echo ═══════════════════════════════════════
python ..\test_ollama_debug.py
if %errorlevel% neq 0 (
    echo ! Ollama connectivity check failed.
    echo ! Please check if the Docker container is running and port 11434 is exposed.
    pause
) else (
    echo ✓ Ollama connectivity verified.
)

:: Save backend directory
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
set "FRONTEND_DIR=%CD%"

:: Kill processes on ports if needed
echo.
echo Checking for processes on ports 8001 and 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /F /PID %%a >nul 2>&1

echo.
echo ═══════════════════════════════════════
echo Starting Servers (Background Mode)...
echo ═══════════════════════════════════════

:: Start Backend (Replicating dev.bat but minimized)
echo Starting backend server...
start "Roddle Backend" /min cmd /k "set OLLAMA_MODEL=%OLLAMA_MODEL%&& "%BACKEND_DIR%\start-backend-with-log.bat" "%BACKEND_DIR%""

:: Start Frontend (Replicating dev.bat but minimized)
echo Starting frontend server...
start "Roddle Frontend" /min cmd /k ""%FRONTEND_DIR%\start-frontend-with-log.bat" "%FRONTEND_DIR%""

:: Wait for services to start
echo.
echo Waiting for services to initialize...
timeout /t 10 /nobreak > nul

:: Check if services are running
echo.
echo Checking service status...

netstat -ano | findstr ":8001" > nul
if %errorlevel% equ 0 (
    echo ✓ Backend running on http://localhost:8001
) else (
    echo ! Backend may not have started. Check backend\backend.log
)

netstat -ano | findstr ":3000" > nul
if %errorlevel% equ 0 (
    echo ✓ Frontend running on http://localhost:3000
) else (
    echo ! Frontend may not have started. Check frontend\frontend.log
)

echo.
echo ═══════════════════════════════════════
echo ✓ All services started in background!
echo ═══════════════════════════════════════
echo.
echo 📱 Opening Game: http://localhost:3000
echo.

:: Open browser ONCE
start http://localhost:3000

echo Press any key to stop all services...
pause > nul

echo.
echo Stopping services...
taskkill /F /IM python.exe > nul 2>&1
taskkill /F /IM node.exe > nul 2>&1
docker-compose down
echo Done.
