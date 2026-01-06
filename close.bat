@echo off
echo Stopping Perplexed services...

:: Find and kill process on port 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Found process %%a on port 8000. Killing...
    taskkill /F /PID %%a
)

echo.
echo Checking for lingering Python processes...
:: Optional: Attempt to kill python processes if they are stuck (Use with caution if running other python apps)
:: taskkill /F /IM python.exe /T

echo.
echo Perplexed has been stopped.
pause
