---
description: n8n 노드 전체 인덱스 및 호환성 매트릭스 (Context7 최신 정보 반영)
---

# n8n Node Index & Compatibility

이 문서는 n8n-skills-2.1.1 스킬팩과 Context7을 통해 확인된 최신 업데이트(v1.73.0+)를 통합한 마스터 인덱스입니다.

## 🌟 최신 업데이트 (v1.73.0+ detected)

Context7을 통해 확인된 주요 변경 사항입니다:

### ✨ 신규 노드
- **Microsoft Outlook Trigger** (`n8n-nodes-base.microsoftOutlookTrigger`): Outlook 이벤트 기반 트리거
- **HTML Node** (`n8n-nodes-base.html`): HTML 생성 및 템플릿 처리 (구 HTML Extract 대체)
- **Ollama Embeddings** (`n8n-nodes-langchain.embeddingsOllama`): 로컬 LLM 임베딩
- **Azure OpenAI Embeddings** (`n8n-nodes-langchain.embeddingsAzureOpenAi`): Azure 기반 임베딩

### 🚀 기능 업데이트
- **Gmail / Slack**: `Send and wait` 오퍼레이션 추가 (이메일/메시지 보내고 응답 대기 가능)
- **Linear Trigger**: Admin scope 지원 추가
- **Date Functions**: `toDateTime()`, `toInt()` 변환 함수 추가

---

## 🔍 노드 검색 가이드

### 1. 고우선순위 노드 (50개)
자주 사용되는 핵심 노드는 `n8n-nodes-transform.md` 등 별도 파일에 상세 정의되어 있습니다.

| Node Name | Node Type | Category | Description |
|-----------|-----------|----------|-------------|
| **Code** | `nodes-base.code` | Transform | JavaScript/Python 코드 실행 |
| **Webhook** | `nodes-base.webhook` | Trigger | HTTP 요청 수신 |
| **HTTP Request** | `nodes-base.httpRequest` | Output | 외부 API 호출 |
| **Set** | `nodes-base.set` | Transform | 데이터구조 변경 및 변수 설정 |
| **IF** | `nodes-base.if` | Transform | 조건 분기 처리 |
| **Merge** | `nodes-base.merge` | Transform | 데이터 병합 |
| **Google Sheets** | `nodes-base.googleSheets` | Productivity | 시트 읽기/쓰기 |
| **Wait** | `nodes-base.wait` | Misc | 일정 시간 또는 웹훅 대기 |

### 2. 전체 노드 인덱스 (545+개)

나머지 노드는 스킬팩의 `resources/` 내 병합 파일(merged files)에 있습니다.

**읽기 예시:**
```
Read("resources/transform/transform-merged-1.md", offset=110, limit=64)
```

*(참조: 전체 리스트는 `resources/INDEX.md` 파일 참조. 아래는 주요 카테고리별 요약입니다)*

#### AI & LangChain
| Node | Type | Location |
|------|------|----------|
| **AI Agent** | `nodes-langchain.agent` | transform/transform-merged-2.md |
| **OpenAI Chat Model** | `nodes-langchain.lmChatOpenAi` | transform/transform-merged-2.md |
| **Google Gemini Chat** | `nodes-langchain.lmChatGoogleGemini` | transform/transform-merged-3.md |
| **Vector Store** | `nodes-langchain.vectorStore*` | transform/transform-merged-2.md |

#### Data & Utility
| Node | Type | Location |
|------|------|----------|
| **Date & Time** | `nodes-base.dateTime` | transform/transform-merged-1.md |
| **Item Lists** | `nodes-base.itemLists` | transform/transform-merged-1.md |
| **Crypto** | `nodes-base.crypto` | transform/transform-merged-1.md |
| **Spreadsheet File** | `nodes-base.spreadsheetFile` | transform/transform-merged-2.md |

---

## 🔗 노드 호환성 매트릭스 (Compatibility Matrix)

노드 간 연결 가능 여부 (`++`: 권장, `+`: 가능, `X`: 불가)

| Source ↓ / Target → | Code | Function | HTTP | IF | Webhook | Merge | Notion |
|---------------------|------|----------|------|----|---------|-------|--------|
| **Code** | - | + | + | + | X | + | + |
| **Function** | + | - | + | + | X | + | + |
| **HTTP Request** | + | + | - | + | X | + | + |
| **IF** | + | + | + | - | X | + | + |
| **Webhook** | ++ | ++ | ++ | ++ | - | ++ | ++ |
| **Merge** | + | + | + | + | X | - | + |
| **Notion** | + | + | + | + | X | + | - |

**핵심 규칙**:
1. **Trigger/Webhook 노드**는 **Source**(출발점)로만 사용 가능, Target(목적지)가 될 수 없음 (`X`).
2. 대부분의 **Action/Transform 노드**는 서로 자유롭게 연결 가능 (`+`).
3. **Webhook → Any Node** 연결은 가장 강력하고 일반적인 패턴 (`++`).

---

## 사용 팁

- 특정 노드의 상세 설정이 궁금하면 `grep_search`를 사용해 `resources/` 폴더를 검색하세요.
- 최신 기능이 의심되면 `context7` 툴을 사용해 확인하세요.
- AI Agent 관련 노드는 `nodes-langchain` 패키지에 속합니다.
