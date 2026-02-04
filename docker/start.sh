#!/bin/bash
# ============================================
# 🚀 n8n 원클릭 실행 스크립트 (Mac/Linux)
# ============================================
# 사용법: ./start.sh
# ============================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 현재 스크립트 위치로 이동
cd "$(dirname "$0")"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   🚀 n8n 자동화 플랫폼 실행기${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Docker 실행 확인
echo -e "${BLUE}[1/4]${NC} Docker 확인 중..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker가 실행되지 않았습니다!${NC}"
    echo ""
    echo "Docker Desktop을 먼저 실행해주세요:"
    echo "  - Mac: Applications에서 Docker 실행"
    echo "  - 상단 메뉴바에 🐳 고래 아이콘이 보이면 준비 완료"
    echo ""
    exit 1
fi
echo -e "${GREEN}✅ Docker 실행 중${NC}"

# .env 파일 확인/생성
echo -e "${BLUE}[2/4]${NC} 환경 설정 확인 중..."
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env 파일이 없습니다. 기본 설정으로 생성합니다...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env 파일 생성 완료${NC}"
    echo ""
    echo -e "${YELLOW}📝 API 키 설정이 필요한 경우:${NC}"
    echo "   nano .env 또는 open -e .env 로 파일을 열어 수정하세요"
    echo ""
else
    echo -e "${GREEN}✅ 환경 설정 확인 완료${NC}"
fi

# 기존 컨테이너 정리
echo -e "${BLUE}[3/4]${NC} 기존 컨테이너 확인 중..."
if docker ps -a | grep -q "n8n"; then
    echo "   기존 n8n 컨테이너 정리 중..."
    docker-compose down 2>/dev/null || true
fi
echo -e "${GREEN}✅ 준비 완료${NC}"

# n8n 시작
echo -e "${BLUE}[4/4]${NC} n8n 시작 중..."
echo ""
docker-compose up -d

# 시작 대기
echo ""
echo -e "${YELLOW}⏳ n8n 시작 대기 중... (약 10-20초)${NC}"
sleep 5

# 터널 URL 확인
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 n8n이 성공적으로 시작되었습니다!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📍 로컬 접속 주소:${NC}"
echo "   http://localhost:5678"
echo ""

# 터널 모드 확인
if grep -q "N8N_TUNNEL_MODE=true" .env 2>/dev/null; then
    echo -e "${BLUE}🌐 외부 접속 URL 확인 중...${NC}"
    echo "   (터널 URL이 생성되면 아래에 표시됩니다)"
    echo ""
    echo -e "${YELLOW}   터널 URL 확인 명령어:${NC}"
    echo "   docker-compose logs | grep -i tunnel"
    echo ""
    sleep 3
    TUNNEL_URL=$(docker-compose logs 2>&1 | grep -oE "https://[a-zA-Z0-9.-]+\.hooks\.n8n\.cloud" | head -1)
    if [ -n "$TUNNEL_URL" ]; then
        echo -e "${GREEN}🌍 외부 접속 URL:${NC}"
        echo "   $TUNNEL_URL"
        echo ""
    else
        echo -e "${YELLOW}   터널 URL을 찾는 중입니다. 잠시 후 다시 확인하세요:${NC}"
        echo "   docker-compose logs | grep tunnel"
        echo ""
    fi
fi

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📚 자주 쓰는 명령어:${NC}"
echo "   ./start.sh          - n8n 시작"
echo "   ./stop.sh           - n8n 중지"
echo "   ./logs.sh           - 로그 보기"
echo "   ./tunnel-url.sh     - 터널 URL 확인"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
