@echo off
REM PyInstaller build script for Guest Detector
REM This creates an .exe that can be installed as a Windows Service via NSSM

echo Building Guest Detector executable...

REM First, install all dependencies from requirements.txt
echo Installing dependencies...
python -m pip install -r requirements.txt

REM Ensure watchdog is properly installed
python -m pip install watchdog --force-reinstall

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

REM Clean old builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build executable
REM --onefile: Single standalone executable
REM --windowed: No console window
REM --uac-admin: Request admin privileges
REM --collect-all: Collect all hidden imports and data
pyinstaller ^
    --onefile ^
    --uac-admin ^
    --name "VMManagerDetector" ^
    --distpath ./dist ^
    --workpath ./build ^
    --specpath ./build ^
    --collect-all watchdog ^
    --collect-all httpx ^
    --hidden-import=watchdog ^
    --hidden-import=watchdog.observers ^
    --hidden-import=watchdog.observers.polling ^
    --hidden-import=watchdog.events ^
    --hidden-import=httpx ^
    src/main.py

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo.
echo Build successful!
echo Executable location: .\dist\VMManagerDetector.exe
echo.
echo Next steps to install as service:
echo 1. Download NSSM from https://nssm.cc/download
echo 2. Extract nssm.exe to a known location
echo 3. Run: nssm install VMManagerDetector "C:\path\to\dist\VMManagerDetector.exe"
echo 4. Run: nssm set VMManagerDetector AppDirectory "C:\path\to\guest-detector"
echo 5. Run: nssm start VMManagerDetector
echo.
pause
