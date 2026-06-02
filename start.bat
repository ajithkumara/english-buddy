@echo off
cd /d "%~dp0"
echo.
echo  =============================================
echo   English Buddy — Starting local server...
echo  =============================================
echo.
echo  Open this URL in Google Chrome:
echo  http://localhost:8765/frontend/english_buddy.html
echo.
timeout /t 2 /nobreak >nul
start "" "http://localhost:8765/frontend/english_buddy.html"
python backend/server.py
pause
