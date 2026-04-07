@echo off
REM Guest Detector startup script (for testing)

cd /d "%~dp0"

echo ========================================
echo VM Manager Guest Detector
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
    echo HOST_LAN_IP=192.168.1.100
    echo DETECTOR_ID=your_detector_id
    echo VM_SECRET_KEY=your_secret_key
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

REM Run the detector
echo.
echo Starting Guest Detector...
echo.
echo Press Ctrl+C to stop
echo.

python -m src.main

pause
