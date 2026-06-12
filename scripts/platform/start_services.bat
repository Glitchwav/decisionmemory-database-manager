@echo off
REM ============================================================
REM  DecisionMemory Services Launcher
REM  Starts: decisionmemory FastAPI server + mt5_sync.py
REM  Usage:  Run manually or register with Task Scheduler
REM ============================================================

setlocal

REM --- Configuration ---
set PYTHON=C:\Users\johns\AppData\Local\Python312\python.exe
set PROJECT_DIR=C:\Users\johns\projects\decisionmemory-protocol
set LOG_DIR=%PROJECT_DIR%\logs

REM --- Create log directory ---
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM --- Timestamp for log ---
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATESTAMP=%%a-%%b-%%c
echo [%date% %time%] Starting DecisionMemory services... >> "%LOG_DIR%\startup.log"

REM --- Start decisionmemory FastAPI server (background) ---
echo Starting decisionmemory server on port 8000...
cd /d "%PROJECT_DIR%"
start /B "" "%PYTHON%" -m decisionmemory >> "%LOG_DIR%\server.log" 2>&1

REM --- Wait for server to be ready ---
timeout /t 5 /nobreak > nul

REM --- Start mt5_sync.py via watchdog (auto-restart on crash) ---
echo Starting mt5_sync.py (with watchdog auto-restart)...
start /MIN "" "%PROJECT_DIR%\scripts\watchdog_mt5_sync.bat"

echo [%date% %time%] All services started. >> "%LOG_DIR%\startup.log"
echo.
echo DecisionMemory services started:
echo   - decisionmemory server (localhost:8000)
echo   - mt5_sync.py (sync every 60s)
echo.
echo Logs: %LOG_DIR%\
echo Press any key to exit this window (services continue running)...
pause > nul
