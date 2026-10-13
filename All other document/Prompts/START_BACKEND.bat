@echo off
REM Start the FastAPI backend detached with logging (used by agents/scripts)
cd /d "%~dp0backend"
start "Backend - FastAPI (port 8000)" /min cmd /c ".venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 > ..\backend.log 2>&1"
