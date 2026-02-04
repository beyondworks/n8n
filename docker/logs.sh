#!/bin/bash
# ============================================
# 📋 n8n 로그 보기 스크립트 (Mac/Linux)
# ============================================
# Ctrl+C로 종료

cd "$(dirname "$0")"

echo ""
echo "📋 n8n 로그를 표시합니다... (Ctrl+C로 종료)"
echo ""
docker-compose logs -f --tail 100
