![Banner image](https://user-images.githubusercontent.com/10284570/173569848-c624317f-42b1-45a6-ab09-f0ea3c247648.png)

# n8n - 워크플로우 자동화 플랫폼

> 🇰🇷 **한국어** | [English](#english)

n8n은 코드의 유연성과 노코드의 빠른 속도를 동시에 제공하는 워크플로우 자동화 플랫폼입니다.

![n8n.io - Screenshot](https://raw.githubusercontent.com/n8n-io/n8n/master/assets/n8n-screenshot-readme.png)

---

## ✨ 주요 특징

| 기능 | 설명 |
|------|------|
| 🇰🇷 **한국 시간대** | 모든 스케줄이 KST 기준으로 작동 |
| 🌐 **터널링 지원** | 외부에서 Webhook 수신 가능 |
| 📦 **워크플로우 포함** | 뉴스 자동 클리핑 워크플로우 |
| 🔒 **보안 인증** | 기본 인증 지원 |

---

## 🚀 5단계 설치 가이드

### 1️⃣ Docker 설치

**Mac:**
```bash
brew install --cask docker
```
또는 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 다운로드

**Windows:**
[Docker Desktop](https://www.docker.com/products/docker-desktop/) 다운로드 후 설치

---

### 2️⃣ 프로젝트 다운로드

```bash
git clone https://github.com/beyondworks/n8n.git
cd n8n/docker
```

---

### 3️⃣ API 키 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env
```

`.env` 파일을 열어 API 키 입력:

```bash
# API 키 입력
PERPLEXITY_API_KEY=pplx-your-key-here
NOTION_API_KEY=secret_your-key-here
```

**API 키 발급:**
| API | 발급 링크 |
|-----|----------|
| Perplexity | [perplexity.ai](https://www.perplexity.ai/) → Settings → API |
| Notion | [notion.so/my-integrations](https://www.notion.so/my-integrations) |

---

### 4️⃣ 실행

```bash
docker-compose up -d
```

---

### 5️⃣ 접속

브라우저에서 **http://localhost:5678** 접속

🎉 **끝!**

---

## 🌐 외부 접속 (터널링)

외부에서 n8n에 접속하려면:

```bash
# .env 파일에서 터널 활성화
N8N_TUNNEL_MODE=true
```

```bash
# 재시작
docker-compose restart

# 공개 URL 확인
docker-compose logs -f
# 출력: Tunnel URL: https://xxxxx.hooks.n8n.cloud
```

---

## 📦 포함된 워크플로우

### Daily News Clipping (뉴스 자동 클리핑)
- ⏰ 매일 오전 9시 (한국 시간) 자동 실행
- 📰 5개 카테고리: AI, Design, Branding, Build, Marketing
- 📝 Notion 데이터베이스에 자동 저장
- 🇰🇷 한국어 요약 및 핵심 내용 추출

---

## 💻 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `docker-compose up -d` | 시작 |
| `docker-compose down` | 중지 |
| `docker-compose restart` | 재시작 |
| `docker-compose logs -f` | 로그 보기 |

---

## 📖 상세 가이드

더 자세한 설치 가이드는 [docker/README.md](./docker/README.md)를 참고하세요.

---

<br>

---

# English

n8n is a workflow automation platform that gives technical teams the flexibility of code with the speed of no-code.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/beyondworks/n8n.git
cd n8n/docker

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run
docker-compose up -d

# 4. Access
# http://localhost:5678
```

## Features

- 🇰🇷 **Korean Timezone**: All schedules run in KST
- 🌐 **Tunnel Support**: Receive webhooks from external services
- 📦 **Included Workflow**: Daily news clipping automation
- 🔒 **Basic Auth**: Optional security

## External Access (Tunnel)

```bash
# Enable in .env
N8N_TUNNEL_MODE=true

# Restart and check URL
docker-compose restart
docker-compose logs -f
```

## Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start |
| `docker-compose down` | Stop |
| `docker-compose restart` | Restart |
| `docker-compose logs -f` | View logs |

## Detailed Guide

See [docker/README.md](./docker/README.md) for complete installation guide.

---

Made with ❤️ by Beyondworks | Based on [n8n](https://github.com/n8n-io/n8n)
