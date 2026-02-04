@echo off
chcp 65001 > nul
REM ============================================
REM 🌐 터널 URL 확인 스크립트 (Windows)
REM ============================================

cd /d "%~dp0"

echo.
echo 🌐 터널 URL을 확인합니다...
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 아래 로그에서 "hooks.n8n.cloud" 가 포함된 URL을 찾으세요:
echo.
docker-compose logs 2>&1 | findstr /i "tunnel" | findstr /i "http"
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 📋 위에 표시된 URL을 복사해서 어디서든 접속하세요!
echo    - Webhook URL로 사용 가능
echo    - 모바일, 다른 컴퓨터에서 접속 가능
echo.
echo URL이 안 보이면:
echo 1. n8n이 실행 중인지 확인: docker ps
echo 2. 30초 정도 기다린 후 다시 실행
echo.
pause
