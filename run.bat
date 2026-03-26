@echo off
SET VENV_DIR=venv

IF NOT EXIST %VENV_DIR% (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

echo Activating virtual environment...
call %VENV_DIR%\Scripts\activate

echo Checking for software updates...
git pull

echo Installing requirements...
pip install -r requirements.txt

echo Launching Cursor Customizer...
python main.py

pause
