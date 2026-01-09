---
description: n8n 트리거 노드 상세 가이드 (Webhook, Schedule, App Triggers)
---

# n8n Trigger Nodes Guide

트리거 노드는 모든 워크플로우의 시작점입니다. 이 가이드는 가장 자주 사용되는 Webhook, Schedule 트리거와 최신 업데이트된 트리거 정보를 다룹니다.

## ⚡ 핵심 트리거 (Core Triggers)

### 1. Webhook Node (`n8n-nodes-base.webhook`)

외부 시스템에서 HTTP 요청을 받아 워크플로우를 시작합니다.

#### 주요 설정
- **Authentication**:
  - `None`: 인증 없음 (공개)
  - `Basic Auth`: 사용자명/비밀번호
  - `Header Auth`: 특정 헤더 값 확인 (API Key 등)
  - `JWT Auth`: JSON Web Token 검증

- **HTTP Method**: `GET`, `POST`가 가장 일반적. `POST` 사용 시 Body 데이터가 JSON으로 들어옵니다.

- **Response Mode** (응답 설정):
  - `On Received` (즉시 응답): 요청 받자마자 200 OK 반환. (가장 빠름)
  - `Last Node` (최종 노드값): 워크플로우 실행이 끝난 후 마지막 노드의 결과를 반환. (동기식 처리)
  - `Response Node`:중간에 'Respond to Webhook' 노드를 사용하여 동적으로 응답.
  - `Streaming` (v1.x+): AI Agent 등 스트리밍 지원 노드와 함께 사용하여 실시간 응답 (Server-Sent Events 등).

#### 💡 Tip
- **Test URL vs Production URL**:
  - `Test URL`: 워크플로우 편집 화면에서 "Execute Event"를 눌렀을 때만 작동. (일회성)
  - `Production URL`: 워크플로우를 "Active" 상태로 켰을 때 작동. (상시 대기)
  - **주의**: 두 URL이 다릅니다! 배포 시 URL을 꼭 확인하세요.

---

### 2. Schedule Trigger (`n8n-nodes-base.scheduleTrigger`)

정해진 시간이나 주기에 따라 워크플로우를 실행합니다.

#### 주요 모드
- **Interval**: 단순 반복 (예: "매 5분마다", "매 1시간마다")
- **Custom (Cron)**: 정교한 스케줄링.
  - 예: `0 9 * * 1-5` (평일 오전 9시)
  - 예: `*/30 * * * *` (30분마다)
  - 작성 팁: [crontab.guru](https://crontab.guru) 사이트 참조 권장.

---

## 📅 앱 트리거 (App Triggers)

특정 서비스의 이벤트(이메일 수신, 메시지 도착 등)를 감지합니다. 대부분 Polling(주기적 확인) 또는 Webhook 방식을 사용합니다.

### 주요 앱 트리거
| 노드 이름 | 설명 | 비고 |
|-----------|------|------|
| **Telegram Trigger** | 봇에게 메시지가 오면 실행 | Webhook 방식 (실시간) |
| **Slack Trigger** | 채널 메시지, 멘션 등 감지 | App Manifest 설정 필요 |
| **Gmail Trigger** | 새 이메일 수신 시 실행 | Polling 방식 (1분~분 단위 체크) |
| **GitHub Trigger** | Push, PR, Issue 이벤트 | Webhook 방식 |
| **Microsoft Outlook Trigger** | 이메일/캘린더 이벤트 (New!) | v1.31.0+ 추가됨 |

---

## 🛠 워크플로우 구성 팁

1. **트리거는 오직 하나만**: 대부분의 워크플로우는 하나의 트리거로 시작합니다. (단, `Merge` 노드를 사용해 여러 트리거를 합칠 수는 있음)
2. **트리거 데이터 확인**:
   - 워크플로우 작성 시 항상 트리거 노드를 먼저 "Test Step"으로 실행하여 실제 들어오는 데이터 구조(JSON)를 확인하세요.
   - 예: Webhook의 경우 `body`, `query`, `headers` 중 어디에 데이터가 있는지 확인 필수.
3. **오류 처리 (Error Trigger)**:
   - 워크플로우 실패 시 실행되는 별도의 워크플로우(`Error Trigger` 노드 사용)를 만들어두면 운영 안정성이 높아집니다.
