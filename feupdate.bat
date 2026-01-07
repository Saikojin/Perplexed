@echo off
echo ==========================================
echo      Perplexed Frontend Updater
echo ==========================================

echo [1/3] Building Frontend...
cd frontend
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    cd ..
    pause
    exit /b %ERRORLEVEL%
)
cd ..

echo [2/3] Cleaning old backend static files...
if exist backend\static (
    rmdir /s /q backend\static
)
mkdir backend\static

echo [3/3] Copying new build to backend...
xcopy /s /e /y frontend\build\* backend\static\

echo.
echo ==========================================
echo      Update Complete!
echo ==========================================
pause
