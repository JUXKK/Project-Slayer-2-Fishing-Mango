@echo off
cd /d "%~dp0"
if exist JUXK-PS2.exe (
    start "" JUXK-PS2.exe
    exit /b
)
where python >nul 2>nul
if errorlevel 1 (
    echo Run 1-SETUP.bat first.
    pause
    exit /b
)
start "" pythonw main.py
