@echo off
chcp 65001 > nul
REM ============================================
REM 🚀 n8n 원클릭 실행 스크립트 (Windows)
REM ============================================
REM 사용법: start.bat 더블클릭 또는 명령프롬프트에서 실행
REM ============================================

cd /d "%~dp0"

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo    🚀 n8n 자동화 플랫폼 실행기
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Docker 실행 확인
echo [1/4] Docker 확인 중...
docker info > nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Docker가 실행되지 않았습니다!
    echo.
    echo Docker Desktop을 먼저 실행해주세요:
    echo   - 시작 메뉴에서 Docker Desktop 검색
    echo   - 시스템 트레이에 🐳 고래 아이콘이 보이면 준비 완료
    echo.
    pause
    exit /b 1
)
echo ✅ Docker 실행 중

REM .env 파일 확인/생성
echo [2/4] 환경 설정 확인 중...
if not exist .env (
    echo ⚠️  .env 파일이 없습니다. 기본 설정으로 생성합니다...
    copy .env.example .env > nul
    echo ✅ .env 파일 생성 완료
    echo.
    echo 📝 API 키 설정이 필요한 경우:
    echo    notepad .env 로 파일을 열어 수정하세요
    echo.
) else (
    echo ✅ 환경 설정 확인 완료
)

REM 기존 컨테이너 정리
echo [3/4] 기존 컨테이너 확인 중...
docker-compose down > nul 2>&1
echo ✅ 준비 완료

REM n8n 시작
echo [4/4] n8n 시작 중...
echo.
docker-compose up -d

REM 시작 대기
echo.
echo ⏳ n8n 시작 대기 중... (약 10-20초)
timeout /t 5 /nobreak > nul

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 🎉 n8n이 성공적으로 시작되었습니다!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 📍 로컬 접속 주소:
echo    http://localhost:5678
echo.
echo 🌐 외부 접속 URL 확인:
echo    tunnel-url.bat 실행 또는
echo    docker-compose logs ^| findstr tunnel
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 📚 자주 쓰는 명령어:
echo    start.bat          - n8n 시작
echo    stop.bat           - n8n 중지
echo    logs.bat           - 로그 보기
echo    tunnel-url.bat     - 터널 URL 확인
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

pause
