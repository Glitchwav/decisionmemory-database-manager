@echo off
REM Start decision_adapter.py in background
cd /d C:\Users\johns\projects\decisionmemory-protocol

REM Create logs directory
if not exist logs mkdir logs

REM Start adapter (redirect to log file)
python scripts/decision_adapter.py >> logs\decision_adapter.log 2>&1
