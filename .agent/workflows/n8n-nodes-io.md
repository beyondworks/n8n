---
description: n8n 입력/출력 노드 상세 가이드 (HTTP, Notion, Sheets, App I/O)
---

# n8n I/O Nodes Guide

외부 서비스와 데이터를 주고받는 핵심 I/O 노드 가이드입니다.

## 🌐 HTTP Request Node (`n8n-nodes-base.httpRequest`)
"만능 열쇠" 노드입니다. n8n에 전용 노드가 없거나, 전용 노드의 기능이 제한적일 때 사용합니다.

### 주요 기능
- **Authentication**:
  - `Generic Credential Type`: Basic, Header, OAuth2 등 직접 설정.
  - **Predefined Credential Type (v0.178+)**: 다른 노드(예: Notion, Slack)의 저장된 자격 증명(Credential)을 재활용할 수 있습니다. (매우 강력한 기능)
- **Import CURL**: `curl` 명령어를 붙여넣으면 자동으로 설정이 채워집니다.
- **Specify Body**: JSON 모드로 직접 Body를 작성하거나, Key-Pair 방식으로 필드를 매핑할 수 있습니다.

---

## 📝 Notion Node (`n8n-nodes-base.notion`)
Notion 페이지 및 데이터베이스를 관리합니다.

### 주요 오퍼레이션
- **Create Database Page**: 데이터베이스에 새 항목 추가.
- **Append After**: 특정 블록 뒤에 내용 추가.
- **Get Database**: 데이터베이스 속성 및 내용 조회.

### 💡 Tip & Troubleshooting
- **ID 찾기**:
  - `Database ID`: URL에서 `https://notion.so/myworkspace/{DatabaseID}?v=...` 부분.
  - `Page ID`: 페이지 URL의 마지막 32자리 UUID.
- **Relation 업데이트 문제 해결**:
  - Notion 노드에서 One-way Relation 등 특정 속성 업데이트가 안 될 경우, **HTTP Request** 노드를 사용하여 Notion API (`PATCH https://api.notion.com/v1/pages/{page_id}`)를 직접 호출하세요.
  - Body 예시: `{"properties": {"MyRelation": {"relation": [{"id": "related_page_id"}]}}}`

---

## 📊 Google Sheets Node (`n8n-nodes-base.googleSheets`)
스프레드시트 데이터 CRUD 작업을 수행합니다.

### 주요 오퍼레이션
- **Append or Update (Upsert)**: 키 값이 있으면 수정하고, 없으면 추가합니다. (가장 많이 사용됨)
- **Get Many Rows**: 데이터를 읽어옵니다. `Range` (예: `A2:F`)를 지정할 수 있습니다.

### ⚠️ 필수 사전 설정
Google Sheets 노드를 사용하려면 Google Cloud Console에서 다음 API를 활성화해야 합니다:
```bash
gcloud services enable sheets.googleapis.com
gcloud services enable drive.googleapis.com
```

---

## 📧 Messaging & Interaction
최신 n8n 버전(v1.0+)에서는 단순 알림을 넘어 **상호작용**이 가능합니다.

### Send and Wait (Gmail / Slack)
- 이메일이나 메시지를 보내고, 상대방이 **버튼을 클릭하거나 답장을 보낼 때까지 워크플로우를 일시 정지**시킬 수 있습니다.
- 승인 프로세스(Approval Workflow) 구현에 최적화되어 있습니다.
