@echo off
:: Flora Focus — Start Backend (Windows)

echo.
echo  Flora Focus — Starting Backend
echo  ===================================

cd /d "%~dp0"

echo  Installing dependencies...
pip install -r requirements.txt

echo.
echo  Backend starting on http://localhost:8000
echo  Leave this window open while using the app.
echo.

python server.py
pause
