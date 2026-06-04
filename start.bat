@echo off
cd /d "%~dp0"
echo.
echo  =============================================
echo   English Buddy — Starting local server...
echo  =============================================
echo.

REM Check API key is set in Windows environment variables
if "%ANTHROPIC_API_KEY%"=="" (
    echo  WARNING: ANTHROPIC_API_KEY not set!
    echo.
    echo  Set it in Windows environment variables:
    echo  1. Search "Edit the system environment variables"
    echo  2. Click Environment Variables
    echo  3. Under User variables - click New
    echo  4. Variable name:  ANTHROPIC_API_KEY
    echo  5. Variable value: sk-ant-your-key-here
    echo  6. Click OK and restart this terminal
    echo.
    pause
    exit /b 1
)

echo  API key found: %ANTHROPIC_API_KEY:~0,8%...
echo  Opening: http://localhost:8765/english_buddy.html
echo  Use Google Chrome only
echo.
echo  Press Ctrl+C to stop the server
echo.

timeout /t 2 /nobreak >nul
start "" "http://localhost:8765/english_buddy.html"
python backend\server.py
pause
