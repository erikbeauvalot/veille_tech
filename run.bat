@echo off
REM Script to run veille_tech with virtual environment (Windows)

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Run the main script with all arguments passed through
python main.py %*
