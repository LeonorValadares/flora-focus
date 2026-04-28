@echo off
:: Flora Focus — Start App (Windows)
echo.
echo  Flora Focus — Starting App
echo  ================================
cd /d "%~dp0"
echo  Installing dependencies (first time takes a minute)...
pip install kivy[base] requests
echo.
echo  Launching Flora Focus...
echo  Make sure the backend window is already open!
echo.
python main.py
pause
