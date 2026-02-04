#!/bin/bash
# ============================================
# 🌐 n8n + 터널링 실행 스크립트 (Mac/Linux)
# ============================================
# ngrok을 사용하여 외부에서 접속 가능한 URL을 생성합니다
# 사용법: ./start-with-tunnel.sh
# ============================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

cd "$(dirname "$0")"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   🌐 n8n + 터널링 실행기${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Docker 확인
echo -e "${BLUE}[1/5]${NC} Docker 확인 중..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker가 실행되지 않았습니다!${NC}"
    echo "Docker Desktop을 먼저 실행해주세요."
    exit 1
fi
echo -e "${GREEN}✅ Docker 실행 중${NC}"

# ngrok 설치 확인
echo -e "${BLUE}[2/5]${NC} ngrok 확인 중..."
if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}⚠️  ngrok이 설치되어 있지 않습니다.${NC}"
    echo ""
    echo "ngrok 설치 방법:"
    echo ""
    echo -e "${CYAN}Mac (Homebrew):${NC}"
    echo "   brew install ngrok/ngrok/ngrok"
    echo ""
    echo -e "${CYAN}또는 공식 사이트:${NC}"
    echo "   https://ngrok.com/download"
    echo ""
    echo "설치 후 다시 실행해주세요."
    exit 1
fi
echo -e "${GREEN}✅ ngrok 설치됨${NC}"

# .env 파일 확인
echo -e "${BLUE}[3/5]${NC} 환경 설정 확인 중..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ .env 파일 생성 완료${NC}"
else
    echo -e "${GREEN}✅ 환경 설정 확인 완료${NC}"
fi

# n8n 시작
echo -e "${BLUE}[4/5]${NC} n8n 시작 중..."
docker-compose down 2>/dev/null || true
docker-compose up -d
sleep 5
echo -e "${GREEN}✅ n8n 시작 완료${NC}"

# 기존 ngrok 프로세스 정리
pkill -f "ngrok http" 2>/dev/null || true
sleep 1

# ngrok 터널 시작
echo -e "${BLUE}[5/5]${NC} 터널 시작 중..."
ngrok http 5678 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
echo $NGROK_PID > /tmp/ngrok.pid
sleep 3

# 터널 URL 가져오기
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*' | head -1 | cut -d'"' -f4)

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 n8n + 터널이 시작되었습니다!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📍 로컬 접속:${NC}"
echo "   http://localhost:5678"
echo ""

if [ -n "$TUNNEL_URL" ]; then
    echo -e "${GREEN}🌍 외부 접속 URL:${NC}"
    echo ""
    echo -e "   ${CYAN}$TUNNEL_URL${NC}"
    echo ""
    echo -e "${BLUE}📋 이 URL로 어디서든 접속 가능합니다:${NC}"
    echo "   - 스마트폰, 태블릿에서 접속"
    echo "   - 다른 컴퓨터에서 접속"
    echo "   - 외부 서비스에서 Webhook 수신"
    echo ""

    # WEBHOOK_URL 자동 설정 안내
    echo -e "${YELLOW}💡 Webhook 사용 시:${NC}"
    echo "   .env 파일에 다음을 추가하세요:"
    echo "   WEBHOOK_URL=$TUNNEL_URL/"
    echo ""
else
    echo -e "${YELLOW}⚠️  터널 URL을 가져오는 중입니다...${NC}"
    echo "   잠시 후 다음 명령어로 확인하세요:"
    echo "   curl -s http://localhost:4040/api/tunnels | grep public_url"
    echo ""
fi

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📚 명령어:${NC}"
echo "   ./stop-tunnel.sh     - n8n과 터널 모두 중지"
echo "   ./tunnel-url.sh      - 터널 URL 다시 확인"
echo ""
echo -e "${YELLOW}⚠️  주의: 터미널을 닫으면 터널이 종료됩니다.${NC}"
echo -e "${YELLOW}   백그라운드로 유지하려면 이 터미널을 열어두세요.${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
