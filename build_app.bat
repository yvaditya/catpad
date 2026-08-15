@echo off
rem Build the standalone CatPad.exe (no Python needed to run it)
cd /d "%~dp0"
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --windowed ^
  --name CatPad --icon "assets\catpad.ico" ^
  --add-data "ui;ui" --add-data "assets;assets" macro_pad.py
echo.
echo Built dist\CatPad.exe
