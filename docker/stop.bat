@echo off
chcp 65001 > nul
REM ============================================
REM 🛑 n8n 중지 스크립트 (Windows)
REM ============================================

cd /d "%~dp0"

echo.
echo 🛑 n8n을 중지합니다...
docker-compose down
echo.
echo ✅ n8n이 중지되었습니다.
echo.
echo 💡 다시 시작하려면: start.bat
echo.
pause
