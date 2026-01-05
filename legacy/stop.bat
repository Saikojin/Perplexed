@echo off
setlocal

echo Stopping Riddle Master services...

:: Kill any process listening on port 8001 (backend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    echo Killing PID %%a on port 8001
    taskkill /F /PID %%a >nul 2>&1 || echo Failed to kill %%a
)

:: Kill any process listening on port 3000 (frontend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    echo Killing PID %%a on port 3000
    taskkill /F /PID %%a >nul 2>&1 || echo Failed to kill %%a
)

:: Stop all Docker containers using docker-compose
echo Stopping Docker containers...
docker-compose down
if %errorlevel% equ 0 (
    echo ✓ Docker containers stopped
) else (
    echo ! Failed to stop containers with docker-compose
)

echo All stop actions attempted.

echo Cleaning up log files...
if exist "backend\*.log" del "backend\*.log" >nul 2>&1
if exist "frontend\*.log" del "frontend\*.log" >nul 2>&1
echo ✓ Log files cleared.
pause
