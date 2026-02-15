# 세션 인수인계 문서

**날짜**: 2026-02-15
**세션 범위**: 세션 1~4 (AWS 구축 → 일정 개선 → 할루시네이션 수정 → 지출 기록 수정)
**브랜치**: `feature/content-repurposing-skill`
**최종 커밋**: `91038a9` (chore: AWS 배포 스크립트 + 개발 문서 정리)

---

## 1. 이번 날 완료한 작업 (세션 1~4)

### 1.1 [세션 1] AWS 24/7 호스팅 구축

- AWS EC2 t2.micro (Ubuntu 24.04 LTS) 인스턴스 생성
- Docker + Docker Compose 설치, Swap 4GB 설정
- n8n + assistant + cloudflared 3서비스 Docker 배포
- Cloudflare Tunnel로 `n8n.leanbot.cloud` 외부 접속 구성
- 초보자용 9단계 AWS 가이드 작성

### 1.2 [세션 2] schedule.py 기능 개선

- **완료 일정 누락 수정**: 프롬프트 + 코드 방어 2중 (완료/미완료 사전 분류 + 헤더에 건수 명시)
- **브리핑 모드 분리**: morning_briefing(09시) + evening_briefing(21시) + daily_briefing(레거시)
- **리마인더 세분화**: 3시간/1시간/30분/10분 전, 허용오차 ±1분
- **배포 스크립트**: `deploy-to-aws.sh` (기본: restart, --rebuild: 재빌드)

### 1.3 [세션 3] 할루시네이션 근본 원인 수정

- **n8n 워크플로우 URL 수정**: "효율이비서-v2 (HTTP)" 워크플로우의 `localhost:8080` → `assistant:8080` (MCP API로 nodeId 기반 업데이트)
- **할루시네이션 체크 스코프 수정**: `force_tool_call=True`인 명령형에서만 작동하도록 변경 (질의형 "어제 뭐했지?"가 오발동되던 문제)
- **에러 세션 오염 방지**: 에러 응답(`⚠️`)은 세션에 저장하지 않음
- **Notion API KST 시간대 수정 (핵심 근본 원인)**:
  - `_query_by_date("2026-02-14")` → `equals` 필터가 datetime 항목을 놓침
  - Notion API는 UTC 기준 필터링 → KST 08:00 = UTC 전날 23:00 → 어제 일정에서 누락
  - 수정: `_to_kst_range()` 헬퍼로 `T00:00:00+09:00` ~ `T23:59:59+09:00` 범위 쿼리
- **방어 헤더**: 모든 시간대 섹션에 `[N건: 항목명]` + "이 리스트에 없는 항목을 말하지 마세요"

### 1.4 [세션 4] finance.py 지출 기록 누락 수정

- **문제**: "원두값 지출 21000원" 기록 시 봇은 "성공적으로 기록되었습니다" 응답 → 실제 Notion에서 안 보임
- **원인**: 레코드 자체는 생성되었으나 `Type` 속성이 `null` → `금액(지출)` formula = 0 → Notion 타임라인 뷰에서 필터됨
- **근본 원인**: AI가 `add_transaction` 호출 시 `type` 파라미터를 누락, 코드에 기본값 없음
- **수정** (코드 레벨 기본값 강제):
  - `Type`: `args.get("type") or "지출"` → 항상 설정됨
  - `When`: `args.get("when") or f"{year}년 {month:02d}월"` → 현재 월 자동
  - `Account`: `args.get("account") or "토스뱅크"` → 기본 계좌 자동
- **기존 레코드 수정**: Notion API로 "원두값" 레코드의 Type = "지출" 직접 패치

---

## 2. 현재 시스템 상태

### 2.1 AWS 서버

| 항목 | 값 |
|------|-----|
| IP | `54.180.68.210` |
| SSH | `ssh -i ~/Downloads/n8n-key.pem ubuntu@54.180.68.210` |
| 프로젝트 경로 | `~/n8n` |
| 에디터 URL | https://n8n.leanbot.cloud |

### 2.2 컨테이너 상태

| 컨테이너 | 상태 | 비고 |
|-----------|------|------|
| assistant | healthy | schedule.py + finance.py 최신 코드 반영 |
| n8n | unhealthy (동작 정상) | Python task runner 미설치 경고 |
| cloudflared | Up | n8n.leanbot.cloud 터널 정상 |

### 2.3 n8n 워크플로우

| 워크플로우 | ID | 상태 |
|-----------|-----|------|
| [SlackBot] 효율이비서 | `DEVA7QA3yPA4_eToWUX4L` | 활성 |
| 효율이비서-v2 (HTTP) | `RrHjn1jNlUyg9imt` | 활성, URL=`assistant:8080` |

### 2.4 Git 상태

- 브랜치: `feature/content-repurposing-skill`
- 커밋 완료, 푸시 완료
- 미추적 파일: `.tmp_assistant_patch/`, `.tmp_workflows/`, `Skill/` (임시 파일)

---

## 3. 다음 세션에서 이어할 작업

### 3.1 [높음] n8n Cron 워크플로우 구성

브리핑/리마인더 코드는 완성. n8n에서 자동 호출하는 워크플로우가 없음:

```
Cron (매일 09:00) → POST http://assistant:8080/invoke
  body: {"domain":"schedule","mode":"morning_briefing"} → Slack 전송

Cron (매일 21:00) → POST http://assistant:8080/invoke
  body: {"domain":"schedule","mode":"evening_briefing"} → Slack 전송

Cron (매 1분) → POST http://assistant:8080/invoke
  body: {"domain":"schedule","mode":"reminder"} → has_reminder 시만 Slack 전송
```

### 3.2 [높음] leanskills 레포 동기화

- `docker/assistant/` 코드를 `~/.claude/skills/beyondworks-assistant/`에 동기화
- leanskills 레포에 커밋 필요 (커밋 규칙에 따라)

### 3.3 [중간] E2E 검증

- Slack에서 "원두값 지출 5000원" → Notion에 Type=지출, 금액(지출)=5000 확인
- Slack에서 "어제 뭐했지?" → 정확한 어제 일정만 응답하는지 확인
- 리마인더 ±1분 허용오차 실용성 확인

### 3.4 [낮음] deploy-to-aws.sh 개선

- 기본 모드(`restart`)가 코드 변경을 반영하지 않는 문제
  - 현재: Dockerfile이 COPY로 코드를 이미지에 포함 → restart만으로는 새 코드 미반영
  - 방안 A: 항상 `--rebuild` (현재 워크어라운드)
  - 방안 B: volumes 마운트로 코드 매핑 (Docker 방식 변경)
  - 방안 C: 기본 모드도 `--build` 포함

### 3.5 [낮음] n8n unhealthy 경고 해결

- 원인: Python task runner 미설치
- 선택지: healthcheck 완화 / Python 3 설치 / task runner 비활성화

---

## 4. 수정 파일 상세

| 파일 | 변경 | 핵심 |
|------|------|------|
| `docker/assistant/domains/schedule.py` | +125/-48 | KST 시간대 수정, 방어 헤더, 브리핑 분리, 리마인더 세분화 |
| `docker/assistant/core/openai_client.py` | +1/-1 | 할루시네이션 체크에 `force_tool_call` 조건 추가 |
| `docker/assistant/server.py` | +6/-5 | 에러 응답 세션 저장 방지 |
| `docker/assistant/domains/finance.py` | +12/-10 | Type/When/Account 코드 레벨 기본값 강제 |
| `docker/docker-compose.yml` | +2 | assistant 포트 8080 노출 |
| `docker/deploy-to-aws.sh` | 신규 | rsync 기반 1커맨드 AWS 배포 |
| n8n 워크플로우 `RrHjn1jNlUyg9imt` | MCP 수정 | URL localhost→assistant |

---

## 5. 잘한 점 (성공 패턴)

### 5.1 근본 원인까지 파고든 디버깅 (세션 3)

"어제 뭐했지?" 할루시네이션의 표면 원인(AI가 지어냄)이 아닌 근본 원인(Notion API에서 데이터가 비어있음)까지 추적.
- 컨텍스트 데이터 확인 → yesterday=[] → Notion 쿼리 분석 → UTC/KST 시간대 문제 발견
- **3단계 수정** 과정에서 각 단계마다 검증 (equals→range→KST range)

### 5.2 MEMORY.md 교훈 #11 반복 적용 (세션 2, 4)

"AI 행동 제어는 프롬프트가 아닌 코드로" 패턴을 2번 연속 적용:
- schedule.py: 완료 일정 포함 여부를 AI 판단에 맡기지 않고 코드에서 사전 분류
- finance.py: Type/When/Account 기본값을 프롬프트 규칙이 아닌 코드에서 강제

### 5.3 배포 후 코드 검증 패턴 확립 (세션 3)

`--rebuild` 후 `docker exec`로 실제 배포된 코드 확인:
```python
docker exec assistant python3 -c "from domains.finance import ...; print(...)"
```
"배포했으니 됐겠지"가 아닌 "코드가 실제로 반영됐는지" 확인하는 습관.

---

## 6. 못한 점 (개선 포인트)

### 6.1 deploy-to-aws.sh의 restart vs rebuild 함정

- `deploy-to-aws.sh` 기본 모드(restart)로 배포 → 코드 미반영 → "수정했는데 왜 안 돼?"
- Dockerfile이 COPY로 코드 포함하므로 이미지 재빌드 필수
- **교훈**: Docker 이미지 빌드 방식을 이해하고, 배포 스크립트의 기본 모드가 실제로 코드를 반영하는지 확인

### 6.2 3번의 수정 시도 후 근본 원인 도달 (세션 3)

Notion 쿼리 문제를 한 번에 못 찾고 3단계를 거침:
1. `equals` → `range` (datetime vs date-only 문제)
2. `range` with date-only → still empty (UTC 시간대 문제)
3. `range` with KST → 성공

각 단계에서 "왜 안 되지?"를 더 깊이 분석했으면 1~2단계에서 끝낼 수 있었음.
Notion API의 UTC 기준 필터링은 이미 MEMORY.md #6에서 알고 있었지만 쿼리 함수에 적용하지 않은 것.

### 6.3 기존 데이터 정합성 미확인

finance.py의 Type=null 문제는 이전에 생성된 모든 레코드에 영향.
"원두값" 하나만 패치했지만, 과거 레코드 중 Type=null인 것이 더 있을 수 있음.
일괄 점검/수정 스크립트가 필요.

### 6.4 n8n Cron 워크플로우 아직 미완성

세션 2부터 계속 "다음에 하겠다"고 한 Cron 워크플로우가 4세션째 미완성.
브리핑/리마인더 코드는 있지만 자동 실행 수단이 없어 실제 사용 불가.

---

## 7. 빠른 시작 (다음 세션용)

```bash
# 1. 현재 상태
git status && git log --oneline -3

# 2. 서버 상태
ssh -i ~/Downloads/n8n-key.pem ubuntu@54.180.68.210 "cd ~/n8n && docker compose ps"

# 3. 배포 (코드 변경 후)
/Users/yoogeon/n8n/docker/deploy-to-aws.sh --rebuild  # 항상 rebuild 사용!

# 4. 로그
ssh -i ~/Downloads/n8n-key.pem ubuntu@54.180.68.210 "docker logs assistant --tail=30"

# 5. 테스트
ssh -i ~/Downloads/n8n-key.pem ubuntu@54.180.68.210 'curl -s -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '"'"'{"domain":"finance","message":"테스트 지출 100원","mode":"chat"}'"'"''
```

---

## 8. 실수 기록 (이번 세션에서 추가)

### 실수 13: deploy-to-aws.sh 기본 모드로 배포 후 "적용 안 됨" (세션 3)
- **상황**: schedule.py 수정 후 `deploy-to-aws.sh` (기본 모드)로 배포
- **실수**: 기본 모드 = `docker compose restart` → 기존 이미지 재사용 → 새 코드 미반영
- **원인**: Dockerfile이 COPY로 코드를 이미지에 포함, restart는 이미지 재빌드 안 함
- **교훈**: 코드 변경 시 반드시 `--rebuild` 사용. 또는 배포 스크립트 기본 모드를 항상 빌드로 변경

### 실수 14: Notion 쿼리에 이미 알고 있던 KST 규칙을 미적용 (세션 3)
- **상황**: `_query_by_date()`가 `equals` 필터 사용 → datetime 항목 누락
- **실수**: MEMORY.md #6에 "KST 시간대 처리 3계층"이 있었지만, 쿼리 함수에는 적용 안 됨
- **원인**: 기존 KST 처리는 `_exec_tool`(쓰기)에만 적용, 읽기 쿼리는 누락
- **교훈**: 시간대 처리는 읽기/쓰기 양쪽에 모두 적용해야 함

### 실수 15: finance.py Type=null로 "보이지 않는 레코드" 생성 (세션 4)
- **상황**: AI가 `type` 파라미터를 생략 → Notion에 Type=null 레코드 생성
- **실수**: 프롬프트에 "기본값 지출"이라고만 써놓고 코드에서 강제하지 않음
- **원인**: MEMORY.md 교훈 #11을 finance 도메인에 적용하지 않았음
- **교훈**: 새 도메인 코드 작성 시 기존 교훈 적용 여부를 체크리스트로 확인

---

## 9. 관련 문서

| 문서 | 경로 | 용도 |
|------|------|------|
| AWS 가이드 | [aws-free-tier-setup-guide.md](aws-free-tier-setup-guide.md) | AWS 계정~Docker 설치 |
| 개발 계획 | [Develope.md](Develope.md) | 전체 로드맵 |
| MCP 포스트모템 | [2026-02-08-n8n-ssh-mcp-postmortem.md](2026-02-08-n8n-ssh-mcp-postmortem.md) | n8n MCP 교훈 |
| workspace 방어 | [2026-02-09-workspace-create-record-fix.md](2026-02-09-workspace-create-record-fix.md) | 코드 방어 3층 |
| 할루시네이션 수정 | [hallucination-fix-analysis.md](hallucination-fix-analysis.md) | 감지 로직 스코프 |
