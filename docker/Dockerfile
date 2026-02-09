# n8n Custom Docker Image
# 한국 시간대 + Notion MCP Server 포함

FROM docker.n8n.io/n8nio/n8n:latest

# 한국 시간대 설정
ENV TZ=Asia/Seoul

# Notion MCP Server 설치
USER root
RUN npm install -g @notionhq/notion-mcp-server
USER node

# 커스텀 엔트리포인트 (Notion MCP + n8n 동시 실행)
COPY --chmod=755 entrypoint.sh /home/node/entrypoint.sh
ENTRYPOINT ["/home/node/entrypoint.sh"]

# 기본 포트
EXPOSE 5678
