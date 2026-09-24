@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller --quiet
pyinstaller --onefile --windowed --name JUXK-PS2 main.py
echo.
echo Done: dist\JUXK-PS2.exe
pause
