@echo off
echo ============================================================
echo  UNIFIED COMPLIANCE INTELLIGENCE PLATFORM - BACKEND
echo ============================================================

cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install flask flask-cors networkx python-dotenv --quiet

echo.
echo Starting Flask API on http://localhost:5000
echo Auto-initializing with bundled policy + evidence data...
echo.
python api.py

pause
