@echo off
REM Start both servers for AI Smart Knowledge Management System
cd /d "%~dp0backend"
start "Backend - FastAPI (port 8000)" /min .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
cd /d "%~dp0frontend"
start "Frontend - Next.js (port 3000)" /min npx next start -p 3000
echo Starting servers... the browser will open in a few seconds.
timeout /t 8 >nul
start http://localhost:3000
