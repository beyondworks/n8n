#!/bin/bash
# deploy-to-aws.sh — n8n Docker 서비스를 AWS EC2에 배포
# 사용법: ./deploy-to-aws.sh [--rebuild]
#   --rebuild: Docker 이미지를 다시 빌드 (코드 변경 시)

set -e

SERVER_IP="54.180.68.210"
KEY_FILE="$HOME/Downloads/n8n-key.pem"
REMOTE_DIR="n8n"
SSH_OPTS="-i $KEY_FILE -o StrictHostKeyChecking=no -o ConnectTimeout=10"

REBUILD=false
if [[ "$1" == "--rebuild" ]]; then
    REBUILD=true
fi

echo "=== n8n AWS 배포 ==="
echo "서버: ubuntu@$SERVER_IP"
echo "원격 경로: ~/$REMOTE_DIR"
echo ""

# 1. assistant 코드 동기화
echo "[1/4] assistant 코드 동기화..."
rsync -avz --delete \
    -e "ssh $SSH_OPTS" \
    /Users/yoogeon/n8n/docker/assistant/ \
    ubuntu@$SERVER_IP:~/$REMOTE_DIR/assistant/

# 2. Docker 설정 파일 동기화
echo "[2/4] Docker 설정 동기화..."
scp $SSH_OPTS \
    /Users/yoogeon/n8n/docker/docker-compose.yml \
    /Users/yoogeon/n8n/docker/Dockerfile \
    /Users/yoogeon/n8n/docker/entrypoint.sh \
    ubuntu@$SERVER_IP:~/$REMOTE_DIR/

# 3. 재빌드 또는 재시작
if $REBUILD; then
    echo "[3/4] Docker 이미지 재빌드 + 재시작..."
    ssh $SSH_OPTS ubuntu@$SERVER_IP \
        "cd ~/$REMOTE_DIR && docker compose up -d --build"
else
    echo "[3/4] assistant 컨테이너만 재시작..."
    ssh $SSH_OPTS ubuntu@$SERVER_IP \
        "cd ~/$REMOTE_DIR && docker compose restart assistant"
fi

# 4. 상태 확인
echo "[4/4] 상태 확인..."
sleep 3
ssh $SSH_OPTS ubuntu@$SERVER_IP \
    "cd ~/$REMOTE_DIR && docker compose ps && echo '' && docker compose logs assistant --tail=5"

echo ""
echo "=== 배포 완료 ==="
