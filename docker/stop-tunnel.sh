#!/bin/bash
# ============================================
# 🛑 n8n + 터널 중지 스크립트 (Mac/Linux)
# ============================================

cd "$(dirname "$0")"

echo ""
echo "🛑 n8n과 터널을 중지합니다..."

# ngrok 중지
if [ -f /tmp/ngrok.pid ]; then
    kill $(cat /tmp/ngrok.pid) 2>/dev/null || true
    rm /tmp/ngrok.pid
fi
pkill -f "ngrok http" 2>/dev/null || true

# Docker 중지
docker-compose down

echo ""
echo "✅ n8n과 터널이 중지되었습니다."
echo ""
echo "💡 다시 시작하려면: ./start-with-tunnel.sh"
echo ""
