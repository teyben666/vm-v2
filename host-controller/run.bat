@echo off
REM Host Controller startup script

cd /d "%~dp0"

echo ========================================
echo VM Manager Host Controller
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Please create .env with:
    echo.
    echo TELEGRAM_BOT_TOKEN=your_bot_token
    echo ADMIN_SECRET_TOKEN=your_secret
    echo HOST_LAN_IP=192.168.1.100
    echo API_PORT=8000
    echo.
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Run the host controller
echo.
echo Starting Host Controller...
echo.

python -m src.main

pause
