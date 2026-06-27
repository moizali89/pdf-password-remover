#!/usr/bin/env bash
# PDF Password Remover — launcher for macOS / Linux
# Creates a virtual environment, installs dependencies, and starts the app.
set -e
cd "$(dirname "$0")"

# Find a Python 3 interpreter
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Error: Python 3 is not installed. Install it from https://www.python.org/downloads/"
  exit 1
fi

# Create the virtual environment on first run
if [ ! -d ".venv" ]; then
  echo "Setting up virtual environment (first run only)..."
  "$PYTHON" -m venv .venv
  .venv/bin/python -m pip install --upgrade pip >/dev/null
  .venv/bin/python -m pip install -r backend/requirements.txt
fi

echo "Starting PDF Password Remover at http://127.0.0.1:5000"
echo "Press Ctrl+C to stop."
exec .venv/bin/python -m backend.app
