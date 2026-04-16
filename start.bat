@echo off
title AI Reader - Natural AI Voice
echo.
echo ========================================================
echo   AI Reader v3 - AIMP-Style Native App (Kokoro TTS)
echo ========================================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Create virtual environment if needed
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    echo       Done.
) else (
    echo [1/4] Virtual environment exists.
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install dependencies
echo [2/4] Installing dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
echo       Done.

:: Download models if needed
echo [3/4] Checking AI model files...
python setup.py

:: Launch native app
echo.
echo [4/4] Launching AI Reader...
echo.
echo ========================================================
echo   The app will start in the system tray.
echo   Move mouse to the top of the screen for quick reader.
echo   Right-click tray icon for full reader.
echo ========================================================
echo.
python main.py

pause
