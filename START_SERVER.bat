@echo off
title YT Lead Hunter PRO - Zentic Media
color 0A
echo.
echo  =============================================
echo   YT LEAD HUNTER PRO - ZENTIC MEDIA
echo   Starting Backend Server...
echo  =============================================
echo.

cd /d "%~dp0backend"
echo [*] Checking Python...
python --version
echo.
echo [*] Starting server on http://localhost:8000
echo [*] Press CTRL+C to stop
echo.
start "" "http://localhost:8000"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
