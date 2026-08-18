@echo off
chcp 65001 >/dev/null
echo Starting Personal AI OS...
echo.

echo [1/2] Starting Backend on port 8000...
start "Backend" cmd /k "cd backend && venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 >/dev/null

echo [2/2] Starting Frontend on port 3000...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Services starting...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo.
pause
