@echo off
echo ============================================
echo   OutreachOS Backend - First Time Setup
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to tick "Add Python to PATH" during install
    pause
    exit
)

echo [1/4] Installing Python packages...
pip install flask flask-cors playwright beautifulsoup4 requests lxml

echo.
echo [2/4] Installing Playwright browser (Chromium)...
playwright install chromium

echo.
echo [3/4] Setting your OpenRouter API key...
echo.
echo HOW TO GET YOUR FREE KEY (no card needed):
echo  1. Go to https://openrouter.ai
echo  2. Click Sign In - create a free account
echo  3. Go to Settings then API Keys
echo  4. Click Create Key and copy it
echo  5. Paste it below
echo.
set /p APIKEY="Paste your OpenRouter API key here: "
setx OPENROUTER_API_KEY "%APIKEY%"
set OPENROUTER_API_KEY=%APIKEY%

echo.
echo [4/4] Starting the backend server...
echo.
echo ============================================
echo   Backend running at http://localhost:5000
echo   Open outreach-dashboard-live.html in Chrome
echo   Press Ctrl+C to stop the server
echo ============================================
echo.
python app.py
pause
