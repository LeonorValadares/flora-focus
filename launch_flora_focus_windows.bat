@echo off
setlocal

cd /d "%~dp0"

set "PYTHONW=%~dp0venv\Scripts\pythonw.exe"
set "PYTHON=%~dp0venv\Scripts\python.exe"

if exist "%PYTHONW%" (
    start "" "%PYTHONW%" "%~dp0kivy_app\main.py"
    exit /b 0
)

if exist "%PYTHON%" (
    start "" "%PYTHON%" "%~dp0kivy_app\main.py"
    exit /b 0
)

echo Flora Focus could not find the bundled virtual environment.
echo Expected: venv\Scripts\python.exe
pause
