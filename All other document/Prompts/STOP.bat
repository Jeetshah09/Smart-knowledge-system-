@echo off
REM Stop both servers
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000 .*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 .*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
echo Both servers stopped.
pause
