@echo off
chcp 65001 > nul
REM ============================================
REM 📋 n8n 로그 보기 스크립트 (Windows)
REM ============================================
REM Ctrl+C로 종료

cd /d "%~dp0"

echo.
echo 📋 n8n 로그를 표시합니다... (Ctrl+C로 종료)
echo.
docker-compose logs -f --tail 100
