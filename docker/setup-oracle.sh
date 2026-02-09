#!/bin/bash
# ============================================
# Oracle Cloud Free Tier VM 초기 설정 스크립트
# ============================================
# Ubuntu 22.04 ARM (Ampere A1) 기준
#
# 사용법:
#   ssh ubuntu@<oracle-vm-ip>
#   curl -fsSL https://raw.githubusercontent.com/beyondworks/n8n/master/docker/setup-oracle.sh | bash
#   또는:
#   scp setup-oracle.sh ubuntu@<oracle-vm-ip>:~/ && ssh ubuntu@<oracle-vm-ip> 'bash setup-oracle.sh'
# ============================================

set -euo pipefail

echo "========================================"
echo " Oracle Cloud VM 초기 설정 시작"
echo "========================================"

# 1. 시스템 업데이트
echo "[1/6] 시스템 패키지 업데이트..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# 2. Docker 설치
echo "[2/6] Docker 설치..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    echo "  Docker 설치 완료. 그룹 변경 적용을 위해 재로그인이 필요합니다."
else
    echo "  Docker 이미 설치됨: $(docker --version)"
fi

# 3. Docker Compose 확인 (Docker 최신 버전에 포함)
echo "[3/6] Docker Compose 확인..."
if docker compose version &>/dev/null; then
    echo "  Docker Compose: $(docker compose version)"
else
    echo "  Docker Compose 플러그인 설치..."
    sudo apt-get install -y -qq docker-compose-plugin
fi

# 4. 방화벽 설정 (iptables)
echo "[4/6] 방화벽 설정 (80, 443 포트 오픈)..."
# Oracle Cloud는 기본적으로 iptables가 엄격하게 설정됨
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 5678 -j ACCEPT
# iptables 규칙 영구 저장
sudo sh -c 'iptables-save > /etc/iptables/rules.v4' 2>/dev/null || \
    sudo apt-get install -y -qq iptables-persistent && \
    sudo sh -c 'iptables-save > /etc/iptables/rules.v4'

# 5. 프로젝트 디렉토리 생성
echo "[5/6] 프로젝트 디렉토리 설정..."
PROJECT_DIR="$HOME/beyondworks"
mkdir -p "$PROJECT_DIR"

echo ""
echo "========================================"
echo " 초기 설정 완료!"
echo "========================================"
echo ""
echo "다음 단계:"
echo ""
echo "  1. 재로그인 (Docker 그룹 적용):"
echo "     exit && ssh ubuntu@<oracle-vm-ip>"
echo ""
echo "  2. 프로젝트 파일 복사:"
echo "     scp -r docker/ ubuntu@<oracle-vm-ip>:~/beyondworks/"
echo "     scp -r skills/ ubuntu@<oracle-vm-ip>:~/beyondworks/"
echo ""
echo "  3. 환경 변수 설정:"
echo "     cd ~/beyondworks/docker"
echo "     cp .env.example .env"
echo "     nano .env  # API 키 입력"
echo ""
echo "  4. 서비스 시작:"
echo "     cd ~/beyondworks/docker"
echo "     docker compose -f docker-compose.oracle.yml up -d"
echo ""
echo "  5. 상태 확인:"
echo "     docker compose -f docker-compose.oracle.yml ps"
echo "     docker compose -f docker-compose.oracle.yml logs -f"
echo ""
echo "  6. Oracle Cloud 콘솔에서 Security List 설정:"
echo "     VCN > Security Lists > Default > Ingress Rules에서"
echo "     포트 80, 443 TCP 허용 추가"
echo ""
echo "  7. Slack Event Subscriptions URL 업데이트:"
echo "     http://<oracle-vm-public-ip>/webhook/schedule-assistant"
echo ""
echo "========================================"
