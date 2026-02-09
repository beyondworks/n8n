#!/bin/sh

# ============================================
# n8n + Notion MCP Server Entrypoint
# ============================================
# Notion MCP Server를 백그라운드로 실행한 후 n8n을 시작합니다.

# Notion MCP Server 시작 (NOTION_API_KEY와 MCP_AUTH_TOKEN이 설정된 경우)
if [ -n "$NOTION_API_KEY" ] && [ -n "$MCP_AUTH_TOKEN" ]; then
  echo "[entrypoint] Starting Notion MCP Server on port 3001..."
  NOTION_TOKEN="$NOTION_API_KEY" \
    npx -y @notionhq/notion-mcp-server \
      --transport http \
      --port 3001 \
      --auth-token "$MCP_AUTH_TOKEN" &
  MCP_PID=$!
  sleep 3
  if kill -0 "$MCP_PID" 2>/dev/null; then
    echo "[entrypoint] Notion MCP Server started (PID: $MCP_PID)"
    echo "[entrypoint] Endpoint: http://localhost:3001/mcp"
  else
    echo "[entrypoint] WARNING: Notion MCP Server failed to start"
  fi
else
  echo "[entrypoint] Notion MCP Server skipped (NOTION_API_KEY or MCP_AUTH_TOKEN not set)"
fi

# n8n 시작
echo "[entrypoint] Starting n8n..."
exec n8n start
