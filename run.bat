@echo off
set "VENV_DIR=backend\venv"

if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate"

echo Installing dependencies...
pip install -r backend\requirements.txt

echo Starting Roddle Standalone Server...
python backend\main.py
