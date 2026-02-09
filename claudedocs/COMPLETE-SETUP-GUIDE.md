# 🤖 n8n + AI 자동화 완전 가이드

> **초등학생도 따라 할 수 있는** n8n 워크플로우 자동화 전체 설정 가이드
>
> 작성일: 2026-02-08

---

## 📚 목차

1. [시작하기 전에](#1-시작하기-전에)
2. [Docker로 n8n 설치하기](#2-docker로-n8n-설치하기)
3. [API 키 발급받기](#3-api-키-발급받기)
4. [첫 번째 워크플로우 만들기](#4-첫-번째-워크플로우-만들기)
5. [Notion + Slack 연동하기](#5-notion--slack-연동하기)
6. [Python AI 어시스턴트 설정하기](#6-python-ai-어시스턴트-설정하기)
7. [자연어로 워크플로우 만들기](#7-자연어로-워크플로우-만들기)
8. [문제 해결](#8-문제-해결)

---

## 1. 시작하기 전에

### 1-1. 이 가이드로 뭘 할 수 있나요?

이 가이드를 따라하면 아래 3가지를 자동화할 수 있어요:

| 자동화 | 설명 | 예시 |
|--------|------|------|
| **🔔 알림 자동화** | Slack에 자동으로 메시지 보내기 | "매일 오전 9시 뉴스 요약 보내기" |
| **📝 Notion 자동 관리** | AI가 자동으로 Notion에 저장하기 | "유튜브 영상 → 블로그 글 → Notion 저장" |
| **🤖 AI 비서** | Slack에서 자연어로 명령하기 | "내일 오후 2시 회의 추가해줘" |

### 1-2. 필요한 것들

컴퓨터만 있으면 돼요! (Mac이든 Windows든 상관없어요)

| 항목 | 설명 | 비용 |
|------|------|------|
| **컴퓨터** | Mac 또는 Windows | - |
| **인터넷** | 설치하고 API 키 받을 때 필요 | - |
| **Notion 계정** | 무료 계정 OK | 무료 |
| **OpenAI 계정** | GPT-4 사용 (선택) | $5 무료 크레딧 |
| **Slack 계정** | Slack 알림 (선택) | 무료 |

### 1-3. 시간이 얼마나 걸리나요?

| 단계 | 소요 시간 |
|------|----------|
| Docker 설치 | 5분 |
| n8n 실행 | 2분 |
| API 키 발급 | 10분 |
| 첫 워크플로우 만들기 | 5분 |
| **전체** | **약 20~30분** |

---

## 2. Docker로 n8n 설치하기

### 2-1. Docker가 뭔가요?

Docker는 프로그램을 "상자" 안에 넣어서 어떤 컴퓨터에서든 똑같이 실행할 수 있게 해주는 도구예요.

n8n을 Docker로 실행하면:
- ✅ 설치가 아주 간단해요 (클릭 몇 번이면 끝!)
- ✅ 컴퓨터를 껐다 켜도 자동으로 다시 시작돼요
- ✅ 삭제할 때도 깔끔하게 지울 수 있어요

### 2-2. Docker 설치하기

#### Mac 사용자

1. [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 클릭
2. 파란색 **"Download for Mac"** 버튼 클릭
3. 다운로드된 파일(`.dmg`) 더블클릭
4. Docker 고래 아이콘을 **Applications** 폴더로 드래그
5. **Applications** 폴더에서 **Docker** 더블클릭
6. 상단 메뉴바에 🐳 고래 아이콘이 보이면 성공!

#### Windows 사용자

1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 클릭
2. **"Download for Windows"** 버튼 클릭
3. 다운로드된 설치 파일 더블클릭
4. 설치 중 **"Use WSL 2"** 체크박스를 꼭 체크하세요
5. 설치 완료 후 컴퓨터 재부팅
6. **Docker Desktop** 실행

#### 설치 확인하기

터미널(Mac) 또는 명령 프롬프트(Windows)를 열고 이렇게 입력해보세요:

```bash
docker --version
```

이런 메시지가 나오면 성공이에요:
```
Docker version 24.0.0, build abc123
```

### 2-3. n8n 프로젝트 다운로드

#### 방법 1: Git으로 다운로드 (권장)

터미널에서:

```bash
# 프로젝트 다운로드
git clone https://github.com/beyondworks/n8n.git

# 폴더로 이동
cd n8n/docker
```

#### 방법 2: ZIP 파일로 다운로드

1. https://github.com/beyondworks/n8n 접속
2. 녹색 **"Code"** 버튼 클릭
3. **"Download ZIP"** 클릭
4. 다운로드한 ZIP 파일 압축 해제
5. 터미널에서 `docker` 폴더로 이동:
   ```bash
   cd 다운로드경로/n8n-main/docker
   ```

### 2-4. 환경 설정 파일 만들기

`.env` 파일은 API 키 같은 비밀 정보를 저장하는 파일이에요.

#### Mac/Linux 사용자

```bash
# .env.example 파일을 .env로 복사
cp .env.example .env

# 파일 열기
nano .env
# 또는
open -e .env
```

#### Windows 사용자

```bash
# .env.example 파일을 .env로 복사
copy .env.example .env

# 메모장으로 열기
notepad .env
```

### 2-5. n8n 시작하기

#### Mac/Linux 사용자

```bash
# 원클릭 시작!
./start.sh
```

#### Windows 사용자

```bash
# 원클릭 시작!
start.bat
```

**이런 메시지가 나오면 성공이에요:**

```
✅ Docker is running
✅ Created .env file
✅ Cleaned up old containers
✅ n8n is starting...

🎉 n8n이 시작되었습니다!
   로컬 접속: http://localhost:5678
```

### 2-6. n8n 접속하기

웹 브라우저(크롬, 사파리 등)를 열고 주소창에 입력:

```
http://localhost:5678
```

n8n 화면이 보이면 성공이에요! 🎉

---

## 3. API 키 발급받기

API 키는 n8n이 다른 서비스(Notion, OpenAI 등)와 대화할 수 있게 해주는 "비밀번호" 같은 거예요.

### 3-1. Notion API 키 발급받기

#### Notion이 뭔가요?

Notion은 메모, 문서, 데이터베이스를 한 곳에서 관리할 수 있는 도구예요.
우리는 n8n이 자동으로 Notion에 데이터를 저장하게 만들 거예요.

#### 단계별 가이드

**1단계: Notion 회원가입**

- [notion.so](https://www.notion.so/) 접속
- **"Get Notion Free"** 클릭하여 무료 계정 만들기
- 이메일 인증 완료

**2단계: Integration 만들기**

- [notion.so/my-integrations](https://www.notion.so/my-integrations) 접속
- **"+ New integration"** 클릭
- 이름 입력: `n8n-automation` (아무 이름이나 OK)
- **Type**: `Internal` 선택
- **Submit** 클릭

**3단계: API 키 복사하기**

- **Internal Integration Secret** 복사
- 이렇게 생긴 긴 문자열이에요: `secret_abc123xyz789...`
- ⚠️ **주의**: 이 키는 한 번만 보여줘요. 꼭 복사해서 메모장에 저장하세요!

**4단계: Notion 페이지에 연결하기**

- n8n이 접근할 Notion 페이지 열기 (예: "일정" 페이지)
- 우측 상단 **"···"** 클릭
- **"Connections"** → **"Connect to"** 클릭
- 방금 만든 Integration(`n8n-automation`) 선택

✅ **완료!** 이제 n8n이 이 페이지에 접근할 수 있어요.

**5단계: .env 파일에 추가**

`.env` 파일을 열고 이렇게 입력:

```bash
NOTION_API_KEY=secret_abc123xyz789...
```

### 3-2. OpenAI API 키 발급받기 (선택)

#### OpenAI가 뭔가요?

ChatGPT를 만든 회사예요. AI가 텍스트를 이해하고 생성할 수 있게 해줘요.

#### 단계별 가이드

**1단계: OpenAI 회원가입**

- [platform.openai.com](https://platform.openai.com/) 접속
- **"Sign up"** 클릭하여 계정 만들기
- 이메일 인증 완료

**2단계: API 키 만들기**

- 로그인 후 우측 상단 프로필 클릭
- **"View API keys"** 클릭
- **"+ Create new secret key"** 클릭
- 이름 입력: `n8n-automation`
- **"Create secret key"** 클릭

**3단계: API 키 복사하기**

- 생성된 키 복사: `sk-abc123xyz789...`
- ⚠️ **주의**: 이 키도 한 번만 보여줘요!

**4단계: 결제 수단 등록 (필수)**

- 좌측 메뉴 **"Settings"** → **"Billing"** 클릭
- 신용카드 등록
- 💡 **무료 크레딧**: 처음 가입하면 $5 무료로 줘요 (약 2~3개월 사용 가능)

**5단계: .env 파일에 추가**

```bash
OPENAI_API_KEY=sk-abc123xyz789...
```

### 3-3. Slack API 키 발급받기 (선택)

#### Slack이 뭔가요?

팀 커뮤니케이션 도구예요. n8n이 Slack으로 알림을 보낼 수 있게 만들 거예요.

#### 단계별 가이드

**1단계: Slack 워크스페이스 만들기**

- [slack.com](https://slack.com/) 접속
- **"Get Started"** 클릭
- 워크스페이스 이름 입력 (예: "내 자동화")

**2단계: Slack App 만들기**

- [api.slack.com/apps](https://api.slack.com/apps) 접속
- **"Create New App"** 클릭
- **"From scratch"** 선택
- App Name: `n8n Bot`
- Workspace: 방금 만든 워크스페이스 선택
- **"Create App"** 클릭

**3단계: Bot Token 발급**

- 좌측 메뉴 **"OAuth & Permissions"** 클릭
- **"Scopes"** → **"Bot Token Scopes"**에서 권한 추가:
  - `chat:write` (메시지 보내기)
  - `channels:read` (채널 읽기)
  - `chat:write.public` (공개 채널에 메시지)
- 페이지 위로 스크롤 → **"Install to Workspace"** 클릭
- **"Allow"** 클릭
- **Bot User OAuth Token** 복사: `xoxb-abc123xyz789...`

**4단계: .env 파일에 추가**

```bash
SLACK_BOT_TOKEN=xoxb-abc123xyz789...
```

### 3-4. n8n 재시작하기

API 키를 `.env` 파일에 추가했으면 n8n을 재시작해야 해요:

```bash
# n8n 중지
./stop.sh

# n8n 시작
./start.sh
```

---

## 4. 첫 번째 워크플로우 만들기

이제 본격적으로 워크플로우를 만들어볼 거예요!

### 4-1. 워크플로우가 뭔가요?

워크플로우는 "이렇게 하면 저렇게 해줘"라는 자동화 규칙이에요.

**예시:**
- "매일 오전 9시에" (트리거) → "뉴스를 검색해서" (동작) → "Slack으로 보내줘" (결과)

### 4-2. 간단한 워크플로우 만들기: "매일 Slack 알림"

#### 1단계: 새 워크플로우 만들기

1. n8n 화면(`http://localhost:5678`) 접속
2. 좌측 메뉴 **"Workflows"** 클릭
3. 우측 상단 **"Add workflow"** 클릭

#### 2단계: 트리거 추가하기 (언제 실행할지)

1. **"+"** 버튼 클릭
2. 검색창에 `schedule` 입력
3. **"Schedule Trigger"** 클릭
4. 설정:
   - **Mode**: `Every day`
   - **Hour**: `9` (오전 9시)
   - **Minute**: `0`
5. **"Save"** 클릭

#### 3단계: Slack 노드 추가하기 (무엇을 할지)

1. 트리거 노드 오른쪽 **"+"** 버튼 클릭
2. 검색창에 `slack` 입력
3. **"Slack"** 클릭
4. 설정:
   - **Credential**: `Create New Credential` 클릭
   - **OAuth2 Token**: `.env`에 저장한 `SLACK_BOT_TOKEN` 붙여넣기
   - **Save** 클릭
5. Slack 노드 설정:
   - **Resource**: `Message`
   - **Operation**: `Post`
   - **Channel**: `#general` (채널 선택)
   - **Text**: `좋은 아침입니다! 오늘도 화이팅!`
6. **"Save"** 클릭

#### 4단계: 워크플로우 테스트하기

1. 우측 상단 **"Execute Workflow"** 클릭
2. Slack 채널(`#general`)에 메시지가 도착했는지 확인
3. ✅ 메시지가 도착했으면 성공!

#### 5단계: 워크플로우 활성화하기

1. 워크플로우 이름 입력: `매일 아침 인사`
2. 우측 상단 **"Active"** 토글 켜기 (회색 → 녹색)
3. 🎉 **완료!** 이제 매일 오전 9시에 자동으로 실행돼요!

### 4-3. 워크플로우 가져오기 (Import)

미리 만들어진 워크플로우를 가져올 수도 있어요.

#### 1단계: leanskills 레포 다운로드

```bash
git clone https://github.com/beyondworks/leanskills.git
cd leanskills/workflows
```

#### 2단계: n8n에서 Import

1. n8n 화면 → 좌측 메뉴 **"Workflows"**
2. 우측 상단 **"⋯"** → **"Import from File"**
3. `leanskills/workflows/` 폴더에서 원하는 JSON 파일 선택
   - 예: `daily-news-clipping.json`
4. **"Import"** 클릭

#### 3단계: Credential 설정

워크플로우에서 빨간색 경고가 뜨면:

1. 경고가 있는 노드 클릭
2. **"Credential"** → **"Create New"**
3. API 키 입력 (`.env` 파일에서 복사)
4. **"Save"**

#### 4단계: 워크플로우 활성화

1. 우측 상단 **"Active"** 토글 켜기
2. 완료!

---

## 5. Notion + Slack 연동하기

이제 Slack에서 메시지를 보내면 자동으로 Notion에 저장되게 만들어볼 거예요!

### 5-1. Notion 데이터베이스 만들기

#### 1단계: Notion 페이지 만들기

1. Notion 열기
2. 좌측 **"+ New page"** 클릭
3. 페이지 이름: `일정 관리`

#### 2단계: 데이터베이스 추가

1. 페이지 안에서 `/table` 입력
2. **"Table - Inline"** 선택
3. 테이블 이름: `할 일 목록`

#### 3단계: 속성 추가

기본으로 `Name` 속성이 있어요. 추가 속성을 만들어볼게요:

| 속성 이름 | 타입 | 설명 |
|----------|------|------|
| Name | Title | 할 일 제목 |
| Date | Date | 날짜 |
| Status | Select | 진행 상태 |

**추가 방법:**

1. 테이블 우측 **"+"** 클릭
2. 속성 타입 선택 (Date, Select 등)
3. 이름 입력

#### 4단계: Integration 연결

1. 페이지 우측 상단 **"···"** 클릭
2. **"Connections"** → **"Connect to"**
3. 방금 만든 Integration(`n8n-automation`) 선택

### 5-2. Slack → Notion 워크플로우 만들기

#### 1단계: Slack Webhook 설정

Slack에서 특정 메시지를 보내면 n8n이 실행되게 만들 거예요.

**n8n에서:**

1. 새 워크플로우 만들기
2. **"+"** → `Webhook` 검색
3. **"Webhook"** 노드 추가
4. 설정:
   - **HTTP Method**: `POST`
   - **Path**: `slack-to-notion`
5. **Webhook URL** 복사 (예: `http://localhost:5678/webhook/slack-to-notion`)

**Slack에서:**

1. [api.slack.com/apps](https://api.slack.com/apps) → 만든 App 클릭
2. 좌측 **"Event Subscriptions"** 클릭
3. **"Enable Events"** 켜기
4. **"Request URL"**에 Webhook URL 붙여넣기
   - ⚠️ 외부에서 접근 가능한 URL이 필요해요 (터널링 참고)
5. **"Subscribe to bot events"**에 추가:
   - `message.channels` (채널 메시지)
6. **"Save Changes"**

#### 2단계: Notion 노드 추가

n8n 워크플로우에서:

1. Webhook 노드 오른쪽 **"+"** 클릭
2. `notion` 검색 → **"Notion"** 선택
3. 설정:
   - **Credential**: `Create New`
   - **API Key**: `.env`의 `NOTION_API_KEY` 붙여넣기
   - **Save**
4. Notion 노드 설정:
   - **Resource**: `Database Page`
   - **Operation**: `Create`
   - **Database**: `할 일 목록` 선택
   - **Properties**:
     - `Name`: `{{ $json.event.text }}` (Slack 메시지 내용)
     - `Date`: `{{ new Date().toISOString() }}` (현재 날짜)
     - `Status`: `진행 중`
5. **"Save"**

#### 3단계: 테스트

1. Slack 채널에 메시지 보내기: `테스트: 회의록 작성하기`
2. Notion `할 일 목록` 데이터베이스 확인
3. ✅ 새 항목이 추가되었으면 성공!

---

## 6. Python AI 어시스턴트 설정하기

이제 자연어로 명령할 수 있는 AI 비서를 만들어볼 거예요!

### 6-1. Python 환경 설정

#### 1단계: Python 설치 확인

터미널에서:

```bash
python3 --version
```

**Python 3.9 이상**이 필요해요. 없으면 [python.org](https://www.python.org/downloads/)에서 설치하세요.

#### 2단계: 스킬 다운로드

```bash
# leanskills 레포로 이동
cd /path/to/leanskills

# 스킬 폴더로 이동
cd skills/beyondworks-assistant
```

#### 3단계: 가상 환경 만들기

```bash
# 가상 환경 생성
python3 -m venv .venv

# 가상 환경 활성화 (Mac/Linux)
source .venv/bin/activate

# 가상 환경 활성화 (Windows)
.venv\Scripts\activate
```

#### 4단계: 패키지 설치

```bash
pip install -r requirements.txt
```

### 6-2. 설정 파일 만들기

#### 1단계: 설정 파일 복사

```bash
cp notion_config.json.example notion_config.local.json
```

#### 2단계: API 키 입력

`notion_config.local.json` 파일을 열고 수정:

```json
{
  "notion_api_key": "secret_abc123xyz789...",
  "openai_api_key": "sk-abc123xyz789...",
  "databases": {
    "schedule": "your-schedule-database-id",
    "finance": "your-finance-database-id"
  }
}
```

**Database ID 찾는 방법:**

1. Notion 데이터베이스 페이지 열기
2. 주소창 URL 확인:
   ```
   https://www.notion.so/workspace/abc123xyz789?v=...
                                 ^^^^^^^^^^^^
                                 이 부분이 Database ID
   ```

#### 3단계: 직접 테스트

```bash
python3 assistant.py router "내일 오후 2시 회의 추가해줘" chat
```

**이런 출력이 나오면 성공:**

```json
{
  "response": "✅ 내일 오후 2시에 회의 일정을 추가했습니다.",
  "domain": "schedule"
}
```

### 6-3. n8n에서 Python 호출하기

#### 방법 1: SSH 노드 사용 (로컬)

**1단계: SSH 자격증명 만들기**

n8n에서:

1. 좌측 메뉴 **"Credentials"** 클릭
2. **"+ Add Credential"** → `SSH` 검색
3. 설정:
   - **Name**: `localhost`
   - **Host**: `localhost`
   - **Port**: `22`
   - **Username**: 컴퓨터 사용자 이름
   - **Password**: 컴퓨터 비밀번호
4. **"Save"**

**2단계: SSH 노드 추가**

워크플로우에서:

1. **"+"** → `SSH` 검색
2. 설정:
   - **Credential**: 방금 만든 `localhost`
   - **Command**:
     ```bash
     cd /path/to/skills/beyondworks-assistant && \
     source .venv/bin/activate && \
     python3 assistant.py router "{{ $json.message }}" chat
     ```
3. **"Execute Node"**로 테스트

#### 방법 2: HTTP Request (Docker)

Python 어시스턴트를 웹 서버로 실행하고 n8n이 HTTP로 호출하는 방식이에요.

**1단계: 웹 서버 실행**

```bash
cd skills/beyondworks-assistant
python3 server.py
```

**2단계: HTTP Request 노드 추가**

n8n에서:

1. **"+"** → `HTTP Request`
2. 설정:
   - **Method**: `POST`
   - **URL**: `http://localhost:8000/chat`
   - **Body**: `{{ { "message": $json.message } }}`
3. **"Execute Node"**로 테스트

---

## 7. 자연어로 워크플로우 만들기

드디어! 자연어로 n8n 워크플로우를 만들어볼 거예요.

### 7-1. Claude MCP 설정

#### 1단계: MCP 서버 설치

```bash
# n8n-mcp 설치
cd leanskills/mcp/n8n-mcp
npm install
```

#### 2단계: Claude Code에 MCP 추가

`~/.claude/settings.json` 파일 열기:

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "node",
      "args": ["/path/to/leanskills/mcp/n8n-mcp/dist/index.js"],
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "your-n8n-api-key"
      }
    }
  }
}
```

**n8n API 키 발급:**

1. n8n 화면 → **"Settings"** → **"API"**
2. **"Create API Key"** 클릭
3. 키 복사

#### 3단계: Claude Code에서 자연어로 명령

```
Claude, n8n 워크플로우를 만들어줘:
- 매일 오전 9시에 실행
- Perplexity로 "AI 뉴스" 검색
- 결과를 Slack #general 채널에 전송
```

Claude가 자동으로:

1. n8n 워크플로우 생성
2. Schedule Trigger 추가
3. Perplexity API 노드 추가
4. Slack 노드 추가
5. 워크플로우 활성화

### 7-2. 자주 사용하는 자연어 명령 패턴

| 명령 | 설명 |
|------|------|
| "매일 X시에 Y를 Z로 보내줘" | 스케줄 자동화 |
| "Slack에서 A가 들어오면 Notion에 B로 저장" | Webhook 자동화 |
| "X 데이터를 Y로 변환해서 Z에 저장" | 데이터 변환 |
| "A API에서 데이터 가져와서 B로 필터링" | API 호출 + 필터 |

---

## 8. 문제 해결

### 8-1. Docker 관련

#### "Docker is not running" 오류

**원인**: Docker Desktop이 실행되지 않음

**해결**:
1. Docker Desktop 실행
2. 상단 메뉴바(Mac) 또는 시스템 트레이(Windows)에서 🐳 아이콘 확인
3. 1~2분 기다린 후 다시 시도

#### "포트 5678이 이미 사용 중입니다"

**원인**: 다른 프로그램이 5678 포트를 사용 중

**해결**:

`docker-compose.yml` 파일 수정:

```yaml
ports:
  - "5679:5678"  # 5678 → 5679로 변경
```

접속 URL도 변경:
```
http://localhost:5679
```

### 8-2. API 키 관련

#### "Invalid API Key" 오류

**확인 사항**:

1. API 키를 정확히 복사했는지 (공백 없이)
2. `.env` 파일에 올바르게 저장했는지
3. n8n을 재시작했는지 (`./stop.sh && ./start.sh`)

#### Notion "Cannot access database"

**확인 사항**:

1. Notion 페이지에 Integration 연결 확인
   - 페이지 우측 상단 **"···"** → **"Connections"**
2. Database ID가 올바른지 확인
3. Notion API 키가 유효한지 확인

### 8-3. 워크플로우 관련

#### 워크플로우가 실행되지 않아요

**확인 사항**:

1. 워크플로우가 **Active** 상태인지 (녹색 토글)
2. 모든 노드가 정상인지 (빨간색 경고 없는지)
3. Credential이 모두 설정되었는지

**디버깅 방법**:

1. **"Execute Workflow"** 클릭하여 수동 실행
2. 각 노드를 클릭하여 출력 확인
3. 에러 메시지 읽고 구글 검색

#### SSH 노드에서 "Permission denied"

**원인**: SSH 비밀번호가 틀리거나 SSH 접근이 차단됨

**해결 (Mac)**:

1. **시스템 설정** → **공유**
2. **원격 로그인** 활성화
3. 사용자 이름/비밀번호 확인

**해결 (Windows)**:

SSH 대신 **HTTP Request** 방식 사용 (6-3 참고)

### 8-4. Python 관련

#### "Module not found" 오류

**원인**: 필요한 패키지가 설치되지 않음

**해결**:

```bash
# 가상 환경 활성화
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# 패키지 재설치
pip install -r requirements.txt
```

#### Python 스크립트가 실행되지 않아요

**확인 사항**:

1. Python 경로가 올바른지
2. 가상 환경이 활성화되었는지
3. 파일 권한 확인:
   ```bash
   chmod +x assistant.py
   ```

### 8-5. 로그 확인하기

문제가 계속되면 로그를 확인하세요:

#### n8n 로그 보기

```bash
# 실시간 로그
docker-compose logs -f

# 최근 100줄만
docker-compose logs -f --tail 100
```

#### Python 로그 보기

```bash
# 디버그 모드로 실행
python3 assistant.py router "테스트" chat --debug
```

---

## 9. 다음 단계

축하합니다! 🎉 이제 n8n 자동화 전문가가 되었어요!

### 9-1. 더 배우기

| 주제 | 링크 |
|------|------|
| n8n 공식 문서 | [docs.n8n.io](https://docs.n8n.io) |
| n8n 커뮤니티 | [community.n8n.io](https://community.n8n.io) |
| n8n 템플릿 | [n8n.io/workflows](https://n8n.io/workflows) |
| Notion API 문서 | [developers.notion.com](https://developers.notion.com) |
| OpenAI API 문서 | [platform.openai.com/docs](https://platform.openai.com/docs) |

### 9-2. 프로젝트 아이디어

이제 만들어볼 수 있는 것들:

| 프로젝트 | 설명 | 난이도 |
|---------|------|--------|
| **일일 뉴스 요약** | 매일 뉴스 → 요약 → Slack 전송 | ⭐ 쉬움 |
| **YouTube → 블로그** | 영상 자막 → 블로그 글 → Notion | ⭐⭐ 보통 |
| **고객 문의 자동 응답** | 이메일 수신 → AI 답변 → 자동 발송 | ⭐⭐⭐ 어려움 |
| **소셜미디어 자동 포스팅** | Notion 글 작성 → 여러 SNS 동시 포스팅 | ⭐⭐ 보통 |
| **데이터 대시보드** | API 데이터 수집 → 분석 → 차트 생성 | ⭐⭐⭐ 어려움 |

### 9-3. 커뮤니티

질문이나 도움이 필요하면:

- **GitHub Issues**: [beyondworks/n8n/issues](https://github.com/beyondworks/n8n/issues)
- **이메일**: beyondworks.br@gmail.com

---

## 부록: 빠른 참조

### 자주 쓰는 명령어

| 명령어 | 설명 |
|--------|------|
| `./start.sh` | n8n 시작 (Mac/Linux) |
| `start.bat` | n8n 시작 (Windows) |
| `./stop.sh` | n8n 중지 |
| `./logs.sh` | 로그 보기 |
| `./tunnel-url.sh` | 터널 URL 확인 |
| `docker-compose restart` | n8n 재시작 |
| `docker ps` | 실행 중인 컨테이너 확인 |

### n8n 단축키

| 단축키 | 동작 |
|--------|------|
| `Ctrl + Enter` | 워크플로우 실행 |
| `Ctrl + S` | 저장 |
| `Ctrl + Z` | 실행 취소 |
| `Delete` | 선택한 노드 삭제 |
| `Ctrl + C` | 복사 |
| `Ctrl + V` | 붙여넣기 |

### 환경 변수 템플릿

`.env` 파일 전체 예시:

```bash
# n8n 기본 설정
GENERIC_TIMEZONE=Asia/Seoul
TZ=Asia/Seoul
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=change_this_password

# API 키
PERPLEXITY_API_KEY=pplx-abc123
NOTION_API_KEY=secret_xyz789
OPENAI_API_KEY=sk-proj-abc123
SLACK_BOT_TOKEN=xoxb-abc123

# 터널 설정
N8N_TUNNEL_MODE=true
```

---

**작성**: Beyondworks
**버전**: 1.0.0
**마지막 업데이트**: 2026-02-08

모두의 자동화 여정을 응원합니다! 🚀
