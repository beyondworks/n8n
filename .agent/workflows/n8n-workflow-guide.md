---
description: n8n 워크플로우 제작 가이드 - 노드, 패턴, API 정보 참조
---

# n8n 워크플로우 제작 종합 가이드

n8n 워크플로우를 제작할 때 이 규칙을 참조하세요. 이 문서는 n8n-skills-2.1.1 스킬팩을 기반으로 합니다.

## 스킬팩 리소스 위치

**메인 리소스**: `/Users/yoogeon/Desktop/App build/Claude Skills/n8n-skills-2.1.1/resources/`

| 파일/디렉토리 | 설명 |
|-------------|------|
| **INDEX.md** | 545개 노드 전체 목록, 카테고리별 분류, 라인 번호 정보 |
| **compatibility-matrix.md** | 노드 간 연결 호환성 매트릭스 |
| **guides/usage-guide.md** | 도구 사용법 및 검색 전략 |
| **guides/how-to-find-nodes.md** | 노드 검색 방법 |
| **transform/** | 데이터 변환 노드 (223개) |
| **input/** | 데이터 입력 노드 (110개) |
| **output/** | 데이터 출력 노드 (99개) |
| **trigger/** | 트리거 노드 (108개) |
| **templates/** | 20개 워크플로우 템플릿 (JSON 포함) |
| **community/** | 30개 커뮤니티 패키지 |

---

## 노드 검색 전략

### 시나리오별 검색 방법

| 시나리오 | 검색 방법 |
|---------|----------|
| 특정 서비스 노드 (Gmail, Slack 등) | `resources/**/*gmail*.md` 파일 검색 |
| 기능 요구사항 ("이메일 보내기") | INDEX.md에서 키워드 검색 |
| 카테고리 탐색 ("트리거 노드") | `resources/trigger/README.md` 읽기 |
| 워크플로우 예시 | `resources/templates/` 디렉토리 탐색 |
| 커뮤니티 패키지 | `resources/community/README.md` 확인 |

### 고우선순위 vs 저우선순위 노드

- **고우선순위 (50개)**: 개별 파일, 직접 읽기 (예: `nodes-base.code.md`)
- **저우선순위 (495개)**: 병합 파일, INDEX.md에서 라인 번호 확인 후 특정 범위 읽기

---

## 핵심 노드 상세 정보

### Code 노드 (`n8n-nodes-base.code`)

**설명**: JavaScript 또는 Python 코드 실행

**핵심 속성**:
| 속성 | 값 | 설명 |
|-----|-----|------|
| `mode` | `runOnceForAllItems` / `runOnceForEachItem` | 실행 모드 |
| `language` | `javaScript` / `python` | 언어 선택 |
| `jsCode` | string | JavaScript 코드 |
| `pythonCode` | string | Python 코드 |

**Code 노드 필수 패턴**:
```javascript
// 모든 입력 항목 접근
for (const item of $input.all()) {
  const data = item.json;
  // 처리 로직
}

// 결과 반환 (필수!)
return [{ json: { key: 'value' } }];

// 빈 배열 반환 시 다음 노드 스킵됨
return [];
```

**내장 변수**:
- `$input.all()` - 모든 입력 항목
- `$input.first()` - 첫 번째 입력 항목
- `$today` - 오늘 날짜 (luxon)
- `$now` - 현재 시간
- `$jmespath` - JSON 쿼리

---

### Webhook 노드 (`n8n-nodes-base.webhook`)

**설명**: 외부 웹훅 수신으로 워크플로우 시작

**핵심 속성**:
| 속성 | 옵션 | 설명 |
|-----|------|------|
| `authentication` | `none`, `basicAuth`, `headerAuth`, `jwtAuth` | 인증 방식 |
| `httpMethod` | `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD` | HTTP 메서드 |
| `responseMode` | `onReceived`, `lastNode`, `responseNode` | 응답 시점 |
| `responseData` | `allEntries`, `firstEntryJson`, `firstEntryBinary`, `noData` | 응답 데이터 |

**JSON 예시**:
```json
{
  "name": "Webhook",
  "type": "n8n-nodes-base.webhook",
  "typeVersion": 1,
  "position": [250, 300],
  "parameters": {
    "path": "my-webhook",
    "httpMethod": "POST",
    "responseMode": "onReceived"
  }
}
```

---

### HTTP Request 노드 (`n8n-nodes-base.httpRequest`)

**설명**: HTTP 요청 수행 및 응답 반환

**핵심 속성**:
| 속성 | 옵션 | 설명 |
|-----|------|------|
| `method` | `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `OPTIONS`, `HEAD` | HTTP 메서드 |
| `authentication` | `none`, `predefinedCredentialType`, `genericCredentialType` | 인증 |
| `contentType` | `json`, `form-urlencoded`, `multipart-form-data`, `raw`, `binaryData` | 본문 타입 |

**JSON 예시**:
```json
{
  "name": "HTTP Request",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4,
  "position": [450, 300],
  "parameters": {
    "url": "https://api.example.com/data",
    "method": "POST",
    "authentication": "none",
    "contentType": "json",
    "body": "={{ JSON.stringify($json) }}"
  }
}
```

---

### Notion 노드 (`n8n-nodes-base.notion`)

**설명**: Notion API 연동

**주요 작업**:
| Operation | Value | 설명 |
|-----------|-------|------|
| 블록 추가 | `append` | 블록 뒤에 추가 |
| 자식 블록 조회 | `getAll` | 모든 자식 블록 가져오기 |
| 데이터베이스 조회 | `databasePage.getAll` | DB 페이지 목록 |
| 페이지 생성 | `databasePage.create` | 새 페이지 생성 |
| 페이지 업데이트 | `databasePage.update` | 페이지 수정 |

**Database ID 설정**:
```json
"databaseId": {
  "__rl": true,
  "value": "242003c7-f7be-804a-9d6e-f76d5d0347b4",
  "mode": "list",
  "cachedResultName": "Beyond_Tasks"
}
```

---

## 노드 호환성 매트릭스

연결 호환성 표기:
- `++` 높은 호환성 (권장)
- `+` 보통 호환성 (연결 가능)
- `X` 비호환 (연결 불가)
- `-` 해당 없음 (동일 노드)

**주요 규칙**:
1. **트리거 노드는 워크플로우 시작에만 배치** (다른 노드 뒤에 연결 불가)
2. **Webhook 노드는 모든 액션 노드와 높은 호환성** (`++`)
3. **대부분의 액션 노드는 상호 연결 가능** (`+`)

---

## AI 에이전트 워크플로우 구조

### 기본 AI Agent 패턴

```
Chat Trigger ─[main]─> AI Agent
                         ↑
                         ├─[ai_languageModel]─ LLM (Gemini/OpenAI/Anthropic)
                         ├─[ai_memory]─ Memory (Buffer/Redis/Postgres)
                         └─[ai_tool]─ Tools (HTTP Request/Code/etc.)
```

### AI Agent 연결 타입

| 연결 타입 | 설명 |
|----------|------|
| `main` | 일반 데이터 흐름 |
| `ai_languageModel` | LLM 연결 (필수) |
| `ai_memory` | 대화 기억 (선택) |
| `ai_tool` | 에이전트 도구 (선택, 여러 개 가능) |

### AI Agent JSON 예시

```json
{
  "name": "AI Agent",
  "type": "@n8n/n8n-nodes-langchain.agent",
  "typeVersion": 2.2,
  "position": [400, 300],
  "parameters": {
    "options": {
      "systemMessage": "You are a helpful assistant..."
    }
  }
}
```

### LLM 노드들

| 노드 | nodeType | 설명 |
|-----|----------|------|
| OpenAI Chat Model | `n8n-nodes-langchain.lmChatOpenAi` | GPT-4 등 |
| Google Gemini | `n8n-nodes-langchain.lmChatGoogleGemini` | Gemini Pro |
| Anthropic | `n8n-nodes-langchain.lmChatAnthropic` | Claude |
| Ollama | `n8n-nodes-langchain.lmChatOllama` | 로컬 LLM |

### Memory 노드들

| 노드 | nodeType | 설명 |
|-----|----------|------|
| Simple Memory | `n8n-nodes-langchain.memoryBufferWindow` | n8n 메모리 저장 |
| Redis Memory | `n8n-nodes-langchain.memoryRedisChat` | Redis 저장 |
| Postgres Memory | `n8n-nodes-langchain.memoryPostgresChat` | PostgreSQL 저장 |

---

## 인기 워크플로우 템플릿 (20개)

### AI & Chatbots (15개)
- Build Your First AI Agent (99,862 views)
- AI-Powered WhatsApp Chatbot with RAG
- Gmail AI Email Manager
- Local Chatbot with RAG
- Voice AI Chatbot with ElevenLabs

### Social Media & Video
- Automate Multi-Platform Social Media (205,470 views)
- Clone Viral TikToks with AI Avatars
- Generate AI Videos with Veo3

### Data Processing
- Google Sheets Integration
- Database Sync Workflows

### Communication
- Email Automation
- WhatsApp/Telegram Integration

**템플릿 사용**: `resources/templates/` 디렉토리에서 전체 JSON 확인 가능

---

## 워크플로우 JSON 완전 구조

```json
{
  "name": "워크플로우 이름",
  "nodes": [
    {
      "id": "고유-uuid",
      "name": "노드 표시 이름",
      "type": "n8n-nodes-base.xxx",
      "typeVersion": 2,
      "position": [x, y],
      "parameters": {
        // 노드별 설정
      },
      "credentials": {
        "credentialType": {
          "id": "credential-id",
          "name": "Credential Name"
        }
      }
    }
  ],
  "connections": {
    "소스노드이름": {
      "main": [[{"node": "타겟노드이름", "type": "main", "index": 0}]]
    }
  },
  "settings": {
    "executionOrder": "v1",
    "callerPolicy": "workflowsFromSameOwner"
  }
}
```

---

## n8n REST API

### 인증
```bash
-H "X-N8N-API-KEY: <API_KEY>"
```

### 주요 엔드포인트

| 작업 | 메서드 | URL |
|-----|-------|-----|
| 워크플로우 목록 | GET | `/api/v1/workflows` |
| 워크플로우 조회 | GET | `/api/v1/workflows/{id}` |
| 워크플로우 생성 | POST | `/api/v1/workflows` |
| 워크플로우 업데이트 | PUT | `/api/v1/workflows/{id}` |
| 워크플로우 활성화 | PATCH | `/api/v1/workflows/{id}` + `{"active": true}` |
| 실행 목록 | GET | `/api/v1/executions` |
| 실행 상세 | GET | `/api/v1/executions/{id}?includeData=true` |

### 예시: 워크플로우 생성

```bash
curl -X POST \
  -H "X-N8N-API-KEY: <API_KEY>" \
  -H "Content-Type: application/json" \
  -d @workflow.json \
  http://localhost:5678/api/v1/workflows
```

---

## 커뮤니티 패키지 (30개)

| 패키지 | 카테고리 | 설명 |
|-------|---------|------|
| n8n-nodes-evolution-api | Communication | WhatsApp 통합 |
| n8n-nodes-elevenlabs | AI Tools | 음성 생성 |
| n8n-nodes-chatwoot | Communication | 채팅 플랫폼 |
| n8n-nodes-pdfkit | Document | PDF 생성 |
| @mendable/n8n-nodes-firecrawl | Web Scraping | 웹 스크래핑 |
| n8n-nodes-tavily | AI Tools | AI 검색 |

---

## Best Practices

1. **고우선순위 노드 우선 사용** - 더 안정적이고 문서화 완비
2. **트리거 노드는 시작에만 배치** - 중간 연결 불가
3. **Code 노드에서 항상 return 문 사용** - `return []`은 워크플로우 종료
4. **AI Agent 도구는 10-15개 이하** - 너무 많으면 신뢰성 저하
5. **복잡한 로직은 구조화된 워크플로우로** - AI Agent보다 신뢰성 높음
6. **자격 증명은 n8n UI에서 설정** - API로 생성 불가
7. **호환성 매트릭스 확인** - 연결 전 compatibility-matrix.md 참조

---

## 현재 n8n 인스턴스 정보

- **URL**: http://localhost:5678
- **데이터베이스**: ~/.n8n/database.sqlite
- **서비스 관리**: pm2 (자동 시작 설정됨)
- **API Key**: Settings > API에서 생성
- **기존 워크플로우**: "노션 마감일 리마인더 (이메일)"
