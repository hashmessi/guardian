@echo off
REM Process Guardian - one command to get the demo on screen.
REM Starts the engine, then the UI, in two windows. No network needed.
setlocal
cd /d "%~dp0"

echo [1/3] Checking Python dependencies...
python -c "import fastapi, uvicorn, numpy, sklearn" 2>nul
if errorlevel 1 (
  echo     Missing packages. Installing from pyproject...
  python -m pip install -e . || goto :fail
  python -m pip install "fastapi>=0.143" uvicorn || goto :fail
)

echo [2/3] Starting the Process Guardian engine on port 8000...
start "Process Guardian engine" cmd /k "cd /d "%~dp0" && set PYTHONPATH=src&& python -m uvicorn process_guardian.api.app:app --port 8000"

echo [3/3] Starting the UI on port 5173...
if not exist "frontend\node_modules" (
  echo     Installing UI dependencies, one time only...
  cd frontend && call npm install || goto :fail
  cd ..
)
start "Process Guardian UI" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo   Engine:  http://localhost:8000/api/health
echo   UI:      http://localhost:5173
echo.
echo   Give it a few seconds, then open the UI. If the UI says "No live data",
echo   the engine window will say why.
echo.
exit /b 0

:fail
echo.
echo   Setup failed. Read the error above; the engine was not started.
exit /b 1
