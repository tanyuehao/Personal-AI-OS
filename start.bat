@echo off
chcp 65001 >nul
echo Personal AI OS - Quick Start
echo ==============================

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Please install Docker first: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

if not exist backend\.env (
    echo [INFO] Creating .env file...
    copy backend\.env.example backend\.env
    echo [INFO] Please edit backend\.env to configure your API Key
    echo.
    echo Recommended:
    echo 1. DeepSeek: https://platform.deepseek.com/
    echo 2. SiliconFlow: https://siliconflow.cn/
    echo.
)

echo [INFO] Starting services...
docker-compose up -d

echo.
echo [SUCCESS] Services started!
echo.
echo Access:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
echo First time setup:
echo 1. Edit backend\.env with your API Key
echo 2. Restart: docker-compose restart backend
echo.
pause
