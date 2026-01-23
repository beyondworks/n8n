# n8n Custom Docker Image
# 한국 시간대 및 추가 패키지가 포함된 n8n 이미지

FROM docker.n8n.io/n8nio/n8n:latest

# 추가 패키지 설치 (curl 등)
USER root
RUN apk add --no-cache \
    curl \
    tzdata

# 한국 시간대 설정
ENV TZ=Asia/Seoul
RUN cp /usr/share/zoneinfo/Asia/Seoul /etc/localtime && \
    echo "Asia/Seoul" > /etc/timezone

USER node

# 워크플로우 디렉토리 생성
RUN mkdir -p /home/node/workflows

# 기본 포트
EXPOSE 5678
