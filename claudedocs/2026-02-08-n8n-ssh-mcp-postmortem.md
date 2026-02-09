# n8n SSH 노드 MCP 업데이트 장애 포스트모템

> 작성일: 2026-02-08
> 기간: 2026-02-07 ~ 2026-02-08 (2세션)
> 심각도: P0 (서비스 완전 중단)
> 최종 상태: 900e756 롤백 후 정상 복구

---

## 1. 타임라인

| 시간 | 이벤트 | 영향 |
|------|--------|------|
| 02-07 13:03 | 워크플로우 버전 430 — 마지막 정상 동작 상태 | - |
| 02-07 15:02 | 실행 #1598 — 정상 (12032ms, stdout 정상) | 마지막 성공 실행 |
| 02-07 ~15:30 | MCP `partial_workflow` 업데이트로 SSH 커맨드 이스케이프 깨짐 | SSH 노드 `itemsOutput: 0` |
| 02-07 ~15:45 | MCP `full_workflow` 롤백 시도 #1 — Slack 노드 구조 불일치 | WorkflowHasIssuesError, 모든 실행 실패 |
| 02-07 15:49 | MCP `full_workflow` 롤백 시도 #2 — Slack 노드 수정 | 워크플로우 활성화 성공 |
| 02-07 15:52 | 실행 #1631 — skip:false, SSH 노드 도달 | 파이프라인 정상 복구 |
| 02-08 00:47 | 실행 로그 확인 — Python 정상 호출 (debug_execution.log) | 최종 복구 확인 |

---

## 2. 장애 원인 분석

### 근본 원인: MCP API의 JSON 직렬화가 n8n SSH 표현식의 이스케이프를 변형

```
정상 (n8n UI에서 설정):
$json.message.replace(/"/g, '\\"')

깨진 버전 (MCP partial_update 후):
$json.message.replace(/\\"/g, '\\\\\\"')
```

MCP n8n 도구(`n8n_update_partial_workflow`, `n8n_update_full_workflow`)가 JSON payload를 직렬화할 때 백슬래시가 이중/삼중 이스케이프되는 문제가 발생. n8n 내부적으로 이 값을 다시 파싱하면서 원래 의도와 다른 정규식이 됨.

### 2차 원인: Slack 노드 파라미터 스키마 불일치

```javascript
// 파일에 저장된 형식 (n8n 1.x 호환)
"channel": { "__rl": true, "mode": "id", "value": "={{ $json.channel }}" }

// n8n 2.x가 요구하는 형식
"select": "channel",
"channelId": { "__rl": true, "mode": "id", "value": "={{ $json.channel }}" }
```

leanskills 레포의 JSON 파일은 `"channel"` 키를 사용했으나, 실제 n8n 2.x는 `"select"` + `"channelId"` 구조를 요구. 이 불일치로 WorkflowHasIssuesError 발생.

### 3차 원인: Slack retry를 장애로 오진

실행 목록에서 skip:true가 반복되어 "SSH 노드가 여전히 안 된다"고 오판. 실제로는:
- skip:true 실행들 = 장애 기간 메시지의 Slack retry (x-slack-retry-num 헤더)
- 새 메시지(retry 아닌)는 정상 처리 중이었음

---

## 3. 핵심 실수 3가지

### 실수 1: MCP API로 n8n SSH 표현식 수정

**무엇을 했는가**: `mcp__n8n-mcp__n8n_update_partial_workflow`로 SSH 커맨드의 이스케이프 패턴 수정 시도

**왜 잘못되었는가**: MCP 도구는 JSON 직렬화 레이어를 거치므로, 백슬래시 기반 정규식 표현이 예측 불가능하게 변형됨. 같은 문자열을 보내도 n8n이 받는 값이 다름.

**올바른 접근**: SSH 노드처럼 이스케이프가 민감한 표현식은 n8n UI에서 직접 수정해야 함. MCP API는 단순 문자열 파라미터(이름, 설명 등)에만 안전.

### 실수 2: 검증 없는 full_workflow 롤백

**무엇을 했는가**: leanskills JSON 파일을 그대로 `full_workflow` 업데이트에 사용

**왜 잘못되었는가**:
1. JSON 파일의 Slack 노드 스키마가 n8n 2.x와 불일치
2. JSON 파일의 credential ID가 실제 n8n의 것과 다름 (`cred_ssh_localhost` vs `0oLkHTGQ5CFQzUHY`)
3. 워크플로우 구조를 검증하지 않고 바로 적용

**올바른 접근**: `n8n_get_workflow`로 현재 상태를 먼저 가져온 뒤, 변경이 필요한 노드의 파라미터만 선택적으로 패치. 전체 교체는 최후의 수단.

### 실수 3: 실행 실패 원인 오진 (retry vs 실제 실패)

**무엇을 했는가**: skip:true 실행들을 보고 "워크플로우가 여전히 깨져있다"고 판단

**왜 잘못되었는가**: `x-slack-retry-num` 헤더를 확인하지 않았음. retry 필터가 정상 작동하고 있었고, 새 메시지는 이미 처리되고 있었음.

**올바른 접근**: 실행 실패 분석 시 반드시 (1) HTTP 헤더 확인, (2) 실행 시간 비교, (3) 새 메시지 테스트 — 3단계로 진단.

---

## 4. 교훈과 원칙

### n8n MCP 사용 원칙

| 원칙 | 설명 |
|------|------|
| **이스케이프 불변 원칙** | 정규식, 백슬래시, 따옴표가 포함된 n8n 표현식은 MCP API로 수정하지 않는다. n8n UI에서만 수정한다. |
| **현재 상태 우선 원칙** | `full_workflow` 업데이트 전 반드시 `get_workflow`로 현재 상태를 가져온다. 파일에 저장된 JSON을 그대로 쓰지 않는다. |
| **최소 변경 원칙** | 워크플로우 수정은 `partial_workflow`로 필요한 노드만 패치한다. `full_workflow`는 최후의 수단이다. |
| **자격증명 분리 원칙** | credential ID는 환경마다 다르다. JSON 파일에 저장된 ID를 그대로 사용하지 않는다. |

### Slack 워크플로우 디버깅 원칙

| 원칙 | 설명 |
|------|------|
| **Retry 구분 원칙** | 실행 실패 분석 시 `x-slack-retry-num` 헤더를 반드시 먼저 확인한다. retry와 신규 메시지를 구분한다. |
| **실행 시간 기준 원칙** | SSH 경유 Python 정상 실행 = 10~15초. 300ms 이하 = skip 경로 또는 SSH 미실행. 실행 시간만으로 성공/실패를 빠르게 판단할 수 있다. |
| **E2E 검증 원칙** | 워크플로우 수정 후 반드시 새 메시지를 보내 전체 파이프라인(Slack 수신 → SSH → Python → Slack 응답)을 검증한다. |

### 롤백 원칙

| 원칙 | 설명 |
|------|------|
| **Git 롤백 ≠ n8n 롤백** | Python 코드는 git reset으로 롤백 가능하지만, n8n 워크플로우는 별도 관리가 필요하다. |
| **n8n 버전 스냅샷** | 정상 동작이 확인된 시점의 `get_workflow` 출력을 별도 저장해둬야 한다. JSON 파일 내보내기만으로는 부족하다(스키마 버전, credential ID 차이). |
| **부분 롤백 우선** | 전체 롤백보다 문제된 노드만 이전 상태로 되돌리는 것이 안전하다. |

---

## 5. 현재 시스템 상태 (2026-02-08)

### 정상 동작 확인 항목
- n8n 워크플로우 `gdxmyb96umqRkEF6` 활성화
- SSH 커맨드 이스케이프 정상: `/"/g, '\\"'`
- SSH 자격증명: `0oLkHTGQ5CFQzUHY`
- Slack 노드: `select: channel` + `channelId` (n8n 2.x 호환)
- Python assistant.py: 900e756 상태 (직접 실행 테스트 통과)
- debug_execution.log: 00:47:13 정상 실행 확인

### 900e756 롤백으로 제거된 기능
| 기능 | 설명 | 영향 |
|------|------|------|
| 인라인 메타데이터 | `__u=USER__c=CHANNEL__` 패턴으로 user/channel 전달 | 사용자/채널 식별 불가 → 세션 분리 안 됨 |
| session-scope | `--session-scope universal_v2` | 범용 세션 스코프 미사용 |
| 날짜 자동 기입 | 일정/재무 항목 생성 시 오늘 날짜 자동 추가 | 수동 날짜 입력 필요 |

### 향후 기능 재도입 시 주의사항
1. **인라인 메타데이터**: n8n Code 노드에서 메시지 앞에 메타데이터 추가 → SSH로 전달. n8n SSH 커맨드 자체는 건드리지 않는다.
2. **날짜 자동 기입**: Python 도메인 코드(schedule.py, finance.py)에서만 수정. n8n 워크플로우는 건드리지 않는다.
3. **어떤 기능이든 n8n SSH 커맨드 표현식을 MCP로 수정하지 않는다.**

---

## 6. 빠른 참조

### 정상 동작 기준값
```
실행 #1598 (마지막 정상):
- 실행 시간: 12032ms
- SSH stdout: {"response": "...", "domain": "...", "learning_events": [...]}
- Slack 응답: 정상 전송
```

### n8n 워크플로우 확인 명령
```bash
# 워크플로우 현재 상태 ���인
# → mcp__n8n-mcp__n8n_get_workflow (workflow_id: gdxmyb96umqRkEF6)

# 최근 실행 확인
# → mcp__n8n-mcp__n8n_executions (workflow_id: gdxmyb96umqRkEF6)

# Python 직접 테스트
cd /Users/yoogeon/.claude/skills/beyondworks-assistant
python3 assistant.py router "테스트 메시지" chat
```

### 핵심 식별자
| 항목 | 값 |
|------|-----|
| 워크플로우 ID | `gdxmyb96umqRkEF6` |
| SSH 자격증명 ID | `0oLkHTGQ5CFQzUHY` |
| Slack 자격증명 ID | `67xs3j3Zo3E8M20w` |
| 마지막 정상 버전 | 430 (2026-02-07 13:03:19) |
| 롤백 기준 커밋 | `900e756` (leanskills) |
