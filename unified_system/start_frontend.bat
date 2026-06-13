@echo off
echo ============================================================
echo  UNIFIED COMPLIANCE INTELLIGENCE PLATFORM - FRONTEND
echo ============================================================

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Installing Node dependencies...
    npm install --legacy-peer-deps
)

echo.
echo Starting React app on http://localhost:3000
echo Make sure backend is running on http://localhost:5000
echo.
set REACT_APP_API_URL=http://localhost:5000
.\node_modules\.bin\vite.cmd

pause
