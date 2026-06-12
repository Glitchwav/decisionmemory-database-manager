@echo off
REM ============================================================
REM  Install DecisionMemory Auto-Start Task
REM  Registers a Windows Task Scheduler task to start services
REM  on user login.
REM
REM  Run this script as Administrator (right-click > Run as admin)
REM ============================================================

echo Installing DecisionMemory auto-start task...

schtasks /create /tn "DecisionMemory_AutoStart" /xml "%~dp0DecisionMemory_AutoStart.xml" /f

if %errorlevel%==0 (
    echo.
    echo [OK] Task "DecisionMemory_AutoStart" installed successfully!
    echo     Services will start automatically 30 seconds after login.
    echo.
    echo To manage:
    echo   - View:    schtasks /query /tn "DecisionMemory_AutoStart"
    echo   - Run now: schtasks /run /tn "DecisionMemory_AutoStart"
    echo   - Delete:  schtasks /delete /tn "DecisionMemory_AutoStart" /f
) else (
    echo.
    echo [ERROR] Failed to install task.
    echo Please run this script as Administrator.
)

pause
