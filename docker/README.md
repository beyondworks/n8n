# n8n Docker Setup

n8n 워크플로우 자동화 플랫폼을 Docker로 쉽게 실행하세요.

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/beyondworks/n8n.git
cd n8n/docker
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 API 키 입력
```

### 3. 실행
```bash
docker-compose up -d
```

### 4. 접속
브라우저에서 [http://localhost:5678](http://localhost:5678) 접속

---

## 📋 사전 요구사항

- [Docker](https://www.docker.com/get-started) 설치
- [Docker Compose](https://docs.docker.com/compose/install/) 설치

### Docker 설치 확인
```bash
docker --version
docker-compose --version
```

---

## 🔧 명령어

| 명령어 | 설명 |
|--------|------|
| `docker-compose up -d` | 백그라운드 실행 |
| `docker-compose down` | 중지 |
| `docker-compose logs -f` | 로그 확인 |
| `docker-compose restart` | 재시작 |
| `docker-compose pull && docker-compose up -d` | 업데이트 |

---

## 📁 포함된 워크플로우

### Daily News Clipping (Perplexity + Notion)
- **기능**: 매일 아침 9시 AI/Design/Branding/Build/Marketing 뉴스 자동 클리핑
- **저장**: Notion 데이터베이스
- **필요 API**: Perplexity, Notion

워크플로우 가져오기:
1. n8n 접속 후 Settings → Import from File
2. `workflows/daily-news-clipping.json` 선택

---

## 🔑 API 키 발급 방법

### Perplexity API
1. [perplexity.ai](https://www.perplexity.ai/) 가입
2. Settings → API → API Keys에서 발급

### Notion API
1. [notion.so/my-integrations](https://www.notion.so/my-integrations) 접속
2. New Integration 클릭
3. 이름 입력 후 생성, Secret 복사
4. Notion에서 연동할 페이지에 Integration 연결

---

## 🌏 시간대

기본적으로 **한국 시간대 (Asia/Seoul)**로 설정되어 있습니다.

다른 시간대로 변경하려면 `docker-compose.yml`에서:
```yaml
environment:
  - GENERIC_TIMEZONE=Your/Timezone
  - TZ=Your/Timezone
```

---

## 📞 문의

- GitHub Issues: [링크]
- Email: beyondworks.br@gmail.com
