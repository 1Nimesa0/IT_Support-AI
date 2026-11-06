@echo off
echo ========================================================
echo Starting Voice-Based IT Support Assistant Backend...
echo ========================================================
cd /d "%~dp0\voice-it-support-assistant\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
