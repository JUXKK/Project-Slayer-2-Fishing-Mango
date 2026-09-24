@echo off
title JUXK PS2 - Setup
cd /d "%~dp0"
echo ===== JUXK PS2 SETUP =====
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Installing Python 3.12...
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    echo.
    echo Python installed. Close this window and run 1-SETUP.bat again.
    pause
    exit /b
)

echo Installing packages...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt pyinstaller --quiet
if errorlevel 1 goto fail

echo Building JUXK-PS2.exe...
python -m PyInstaller --onefile --windowed --noconfirm --name JUXK-PS2 main.py
if errorlevel 1 goto fail

copy /y dist\JUXK-PS2.exe JUXK-PS2.exe >nul
echo.
echo Done! Now double-click 2-LAUNCH.bat (or JUXK-PS2.exe).
pause
exit /b

:fail
echo.
echo Setup failed. Screenshot this window and send it.
pause
