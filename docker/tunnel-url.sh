#!/bin/bash
# ============================================
# 🌐 터널 URL 확인 스크립트 (Mac/Linux)
# ============================================

cd "$(dirname "$0")"

echo ""
echo "🌐 터널 URL을 확인합니다..."
echo ""

# ngrok API에서 터널 URL 가져오기
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*' | head -1 | cut -d'"' -f4)

if [ -n "$TUNNEL_URL" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌍 외부 접속 URL:"
    echo ""
    echo "   $TUNNEL_URL"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📋 이 URL을 복사해서 어디서든 접속하세요!"
    echo "   - Webhook URL로 사용 가능"
    echo "   - 모바일, 다른 컴퓨터에서 접속 가능"
    echo ""
    echo "💡 Webhook 사용 시 .env 파일에 추가:"
    echo "   WEBHOOK_URL=$TUNNEL_URL/"
    echo ""
else
    echo "❌ 터널이 실행 중이지 않습니다."
    echo ""
    echo "터널과 함께 시작하려면:"
    echo "   ./start-with-tunnel.sh"
    echo ""
fi
