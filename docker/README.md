# 🚀 n8n 자동화 워크플로우 - 설치 가이드

**초보자도 10분 안에 설치 가능!** Mac과 Windows 모두 지원합니다.

---

## 📋 목차

1. [사전 준비](#1-사전-준비-docker-설치)
2. [프로젝트 다운로드](#2-프로젝트-다운로드)
3. [API 키 발급](#3-api-키-발급)
4. [실행하기](#4-실행하기)
5. [워크플로우 설정](#5-워크플로우-설정)
6. [자주 쓰는 명령어](#6-자주-쓰는-명령어)
7. [문제 해결](#7-문제-해결)

---

## 1. 사전 준비 (Docker 설치)

### Docker란?
> 프로그램을 "상자"에 담아 어떤 컴퓨터에서든 똑같이 실행할 수 있게 해주는 도구입니다.
> Mac, Windows, Linux 어디서든 동일하게 작동합니다.

### Mac 사용자

**방법 1: 공식 설치 (권장)**
1. [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 접속
2. **Download for Mac** 클릭
3. 다운로드된 `.dmg` 파일 실행
4. Docker 아이콘을 Applications 폴더로 드래그
5. Applications에서 Docker 실행
6. 설치 완료 후 상단 메뉴바에 🐳 고래 아이콘 확인

**방법 2: Homebrew로 설치**
```bash
brew install --cask docker
```

### Windows 사용자

1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 접속
2. **Download for Windows** 클릭
3. 다운로드된 설치 파일 실행
4. 설치 중 "Use WSL 2" 옵션 체크 (권장)
5. 설치 완료 후 재부팅
6. Docker Desktop 실행

### 설치 확인
터미널(Mac) 또는 명령 프롬프트(Windows)에서:
```bash
docker --version
# 예시 출력: Docker version 24.0.0, build abc123

docker-compose --version
# 예시 출력: Docker Compose version v2.20.0
```

---

## 2. 프로젝트 다운로드

### 방법 1: Git으로 클론 (권장)
```bash
# 터미널에서 실행
git clone https://github.com/beyondworks/n8n.git
cd n8n/docker
```

### 방법 2: ZIP 다운로드
1. https://github.com/beyondworks/n8n 접속
2. 녹색 **Code** 버튼 클릭
3. **Download ZIP** 클릭
4. 압축 해제 후 `docker` 폴더로 이동

---

## 3. API 키 발급

이 프로젝트는 3개의 API 키가 필요합니다:

| API | 용도 | 필수 여부 |
|-----|------|----------|
| Perplexity | 뉴스 검색 | ✅ 필수 |
| Notion | 데이터 저장 | ✅ 필수 |
| OpenAI | AI 요약 (선택) | ⬜ 선택 |

---

### 3-1. Perplexity API 키 발급

**Perplexity란?** AI 기반 검색 엔진으로, 최신 뉴스와 정보를 검색합니다.

**발급 단계:**

1. [perplexity.ai](https://www.perplexity.ai/) 접속
2. 우측 상단 **Sign Up** 클릭하여 회원가입
3. 로그인 후 좌측 하단 프로필 클릭
4. **Settings** 클릭
5. 좌측 메뉴에서 **API** 클릭
6. **Generate** 버튼 클릭하여 API 키 생성
7. 생성된 키 복사 (예: `pplx-xxxxxxxxxxxx`)

> ⚠️ **주의**: API 키는 한 번만 표시됩니다. 반드시 복사해두세요!

---

### 3-2. Notion API 키 발급

**Notion이란?** 노트, 데이터베이스, 문서를 관리하는 올인원 워크스페이스입니다.

**발급 단계:**

1. [notion.so](https://www.notion.so/) 회원가입 및 로그인
2. [notion.so/my-integrations](https://www.notion.so/my-integrations) 접속
3. **+ New integration** 버튼 클릭
4. 설정:
   - **Name**: `n8n-workflow` (원하는 이름)
   - **Associated workspace**: 사용할 워크스페이스 선택
   - **Type**: Internal
5. **Submit** 클릭
6. **Internal Integration Secret** 복사 (예: `secret_xxxxxxxxxxxx`)

**Notion 페이지에 연결:**
1. n8n이 접근할 Notion 페이지 열기
2. 우측 상단 **···** 클릭
3. **Connections** → **Connect to** 클릭
4. 방금 만든 Integration 선택 (`n8n-workflow`)

---

### 3-3. OpenAI API 키 발급 (선택)

**OpenAI란?** ChatGPT를 만든 회사로, AI 텍스트 생성 서비스를 제공합니다.

**발급 단계:**

1. [platform.openai.com](https://platform.openai.com/) 접속
2. 회원가입 또는 로그인
3. 우측 상단 프로필 → **View API keys** 클릭
4. **+ Create new secret key** 클릭
5. 이름 입력 후 **Create secret key** 클릭
6. 생성된 키 복사 (예: `sk-xxxxxxxxxxxx`)

> 💡 **참고**: OpenAI API는 유료입니다. 무료 크레딧 $5가 제공됩니다.

---

## 4. 실행하기

### 4-1. 환경 변수 설정

```bash
# docker 폴더에서 실행
cd n8n/docker

# .env.example 파일을 .env로 복사
cp .env.example .env
```

### 4-2. API 키 입력

`.env` 파일을 열어 API 키를 입력합니다:

**Mac:**
```bash
nano .env
# 또는
open -e .env
```

**Windows:**
```bash
notepad .env
```

**입력 예시:**
```
PERPLEXITY_API_KEY=pplx-abc123def456
NOTION_API_KEY=secret_xyz789abc123
OPENAI_API_KEY=sk-abc123xyz789
```

저장 후 닫기 (nano 사용 시: `Ctrl+O` → `Enter` → `Ctrl+X`)

### 4-3. n8n 실행

```bash
# docker 폴더에서 실행
docker-compose up -d
```

**출력 예시:**
```
[+] Running 2/2
 ✔ Network docker_default  Created
 ✔ Container n8n           Started
```

### 4-4. 접속 확인

브라우저에서 접속:
```
http://localhost:5678
```

🎉 **n8n 화면이 보이면 성공입니다!**

---

## 5. 워크플로우 설정

### 5-1. 워크플로우 가져오기

1. n8n 접속 (http://localhost:5678)
2. 좌측 메뉴 **Workflows** 클릭
3. 우측 상단 **⋮** → **Import from File** 클릭
4. `workflows/daily-news-clipping.json` 선택
5. **Import** 클릭

### 5-2. 인증 정보 설정

워크플로우에서 빨간색 경고가 표시되면:

1. 경고가 있는 노드 클릭
2. **Credential** 선택 → **Create New Credential** 클릭
3. 해당 서비스의 API 키 입력
4. **Save** 클릭

### 5-3. 워크플로우 활성화

1. 워크플로우 우측 상단 **Active** 토글 켜기
2. 매일 오전 9시에 자동 실행됩니다!

**수동 테스트:**
- **Execute Workflow** 버튼 클릭하여 즉시 실행

---

## 6. 자주 쓰는 명령어

| 명령어 | 설명 |
|--------|------|
| `docker-compose up -d` | n8n 시작 (백그라운드) |
| `docker-compose down` | n8n 중지 |
| `docker-compose restart` | n8n 재시작 |
| `docker-compose logs -f` | 실시간 로그 보기 |
| `docker-compose logs -f --tail 100` | 최근 100줄 로그 |
| `docker-compose pull && docker-compose up -d` | 최신 버전 업데이트 |

---

## 7. 문제 해결

### Docker가 실행되지 않아요
```bash
# Docker Desktop이 실행 중인지 확인
# Mac: 상단 메뉴바에 🐳 아이콘 확인
# Windows: 시스템 트레이에 Docker 아이콘 확인
```

### 포트가 이미 사용 중이에요
```bash
# 5678 포트를 다른 포트로 변경
# docker-compose.yml 파일에서:
ports:
  - "5679:5678"  # 5679로 변경
# 접속: http://localhost:5679
```

### 컨테이너 상태 확인
```bash
docker ps
# n8n 컨테이너가 "Up" 상태인지 확인
```

### 모든 것 초기화
```bash
docker-compose down -v  # 데이터 포함 삭제
docker-compose up -d    # 새로 시작
```

---

## 📞 도움이 필요하신가요?

- **GitHub Issues**: [이슈 등록](https://github.com/beyondworks/n8n/issues)
- **Email**: beyondworks.br@gmail.com

---

Made with ❤️ by Beyondworks
