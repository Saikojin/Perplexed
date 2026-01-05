@echo off
:: Backend logging wrapper
cd /d "%~1"
call venv\Scripts\activate.bat
set PYTHONPATH=%~1
uvicorn server:app --host 127.0.0.1 --port 8001 --reload > backend.log 2>&1
