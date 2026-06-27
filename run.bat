@echo off
REM PDF Password Remover - launcher for Windows
REM Creates a virtual environment, installs dependencies, and starts the app.
setlocal
cd /d "%~dp0"

REM Find a Python interpreter
where python >nul 2>&1
if %errorlevel%==0 (
  set "PYTHON=python"
) else (
  where py >nul 2>&1
  if %errorlevel%==0 (
    set "PYTHON=py -3"
  ) else (
    echo Error: Python 3 is not installed. Install it from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
  )
)

REM Create the virtual environment on first run
if not exist ".venv" (
  echo Setting up virtual environment ^(first run only^)...
  %PYTHON% -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
  ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
)

echo Starting PDF Password Remover at http://127.0.0.1:5000
echo Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m backend.app
endlocal
