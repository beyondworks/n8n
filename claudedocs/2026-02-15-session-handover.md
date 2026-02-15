# 세션 인수인계 문서

**날짜**: 2026-02-15
**세션 목표**: AWS 24/7 서버 운영 방안 조사 + schedule.py 기능 개선 + 서버 배포
**브랜치**: `feature/content-repurposing-skill`

---

## 1. 이번 세션에서 완료한 작업

### 1.1 AWS 24/7 호스팅 조사 및 가이드 작성

- 무료 24/7 호스팅 옵션 비교 분석 (Oracle 제외)
- **결론**: GCP e2-micro(영구 무료, RAM 1GB 빠듯) > Raspberry Pi(초기비용 후 무료) > AWS t2.micro(12개월 무료)
- AWS 초보자 가이드 작성: [aws-free-tier-setup-guide.md](aws-free-tier-setup-guide.md)
  - 계정 생성부터 Docker 설치, 배포, 자동 재시작, 보안 설정까지 9단계 전체 가이드

### 1.2 완료된 일정 누락 버그 수정

- **문제**: "오늘 일정 알려줘" 질문에 AI가 Completed:True 항목을 빼고 "없다"고 답변
- **원인**: Notion API는 정상 반환하지만, LLM이 완료 항목을 자의적으로 제외
- **수정** (프롬프트 + 코드 방어 2중):
  - 프롬프트: "일정 조회 시 완료 항목 포함 규칙" 섹션 추가 (schedule.py:118-121)
  - 코드 방어: 컨텍스트에서 오늘 일정을 미완료/완료로 사전 분류하여 `[총 N건 (미완료 X건, 완료 Y건)]` 형태로 주입 (schedule.py:443-461)
  - AI가 무시할 수 없도록 헤더에 "완료 항목도 반드시 사용자에게 안내할 것" 명시

### 1.3 오전/오후 브리핑 모드 분리

- 기존 `daily_briefing` 1개 → `morning_briefing` + `evening_briefing` 2개로 분리
- `daily_briefing`은 레거시 호환으로 유지 (= morning_briefing과 동일)
- **morning_briefing** (오전 9시용): 인사 + 어제 놓친 일 리마인드 + 오늘 할 일 + 응원
- **evening_briefing** (오후 9시용): 오늘 완료 회고/칭찬 + 미완료 알림 + 내일 미리보기 + 마무리
- 모든 브리핑에 `PLAIN_TEXT_RULE` 적용 (기존에는 누락되어 있었음)
- 변경 위치: schedule.py `_briefing()` (344-388), `handle()` (426)

### 1.4 리마인더 시간대 세분화

- 기존: 1시간/30분/10분 전 (허용 오차 ±10분으로 넓어서 중복 알림 가능)
- 변경: **3시간/1시간/30분/10분** 전, 허용 오차 **±1분**으로 정밀화
- 데이터 구조를 `thresholds` 리스트로 리팩토링하여 확장 용이하게 변경
- 변경 위치: schedule.py `_reminder()` (391-420)

### 1.5 배포 스크립트 작성 + AWS 배포

- `docker/deploy-to-aws.sh` 생성
  - 기본 모드: assistant 코드만 rsync → assistant 컨테이너 재시작 (빠름)
  - `--rebuild` 모드: 전체 Docker 이미지 재빌드 (Dockerfile/compose 변경 시)
- AWS 서버에 수정 코드 배포 완료, assistant 컨테이너 healthy 확인

---

## 2. 현재 시스템 상태 (배포 완료 시점)

### 2.1 AWS 서버

| 항목 | 값 |
|------|-----|
| IP | `54.180.68.210` |
| SSH | `ssh -i ~/Downloads/n8n-key.pem ubuntu@54.180.68.210` |
| 프로젝트 경로 | `~/n8n` (주의: 가이드의 `~/n8n-docker`가 아님) |
| 에디터 URL | https://n8n.leanbot.cloud |
| OS | Ubuntu 24.04 LTS |
| RAM | 914MB + Swap 4GB |
| 디스크 | 29GB (사용 8.7GB, 여유 20GB) |

### 2.2 컨테이너 상태

| 컨테이너 | 상태 | 비고 |
|-----------|------|------|
| assistant | healthy | schedule.py 최신 코드 반영 |
| n8n | unhealthy (동작은 정상) | Python task runner 미설치 경고, HTTP 200 정상 |
| cloudflared | Up | n8n.leanbot.cloud 터널 정상 |

### 2.3 로컬 Git 상태

- 변경된 파일: `docker/assistant/domains/schedule.py`, `docker/docker-compose.yml`
- 새 파일: `docker/deploy-to-aws.sh`
- **커밋 미완료** — 다음 세션 시작 시 커밋 필요

---

## 3. 다음 세션에서 이어할 작업

### 3.1 [높음] n8n Cron 워크플로우 구성

브리핑/리마인더가 코드에만 있고 **n8n 워크플로우에서 자동 호출하는 구성이 없음**.
워크플로우를 만들어야 실제로 동작함:

```
Cron (매일 09:00) → HTTP Request → POST http://assistant:8080/invoke
  body: {"domain":"schedule","mode":"morning_briefing"}
  → Slack 채널에 전송

Cron (매일 21:00) → HTTP Request → POST http://assistant:8080/invoke
  body: {"domain":"schedule","mode":"evening_briefing"}
  → Slack 채널에 전송

Cron (매 1분) → HTTP Request → POST http://assistant:8080/invoke
  body: {"domain":"schedule","mode":"reminder"}
  → has_reminder: true일 때만 Slack 전송
```

- n8n UI(https://n8n.leanbot.cloud)에서 직접 만들거나, MCP `n8n_create_workflow`로 생성
- Slack 채널은 schedule 전용 채널 사용
- 리마인더는 1분 간격이므로 Slack 메시지 중복 방지 로직 고려 필요

### 3.2 [중간] n8n unhealthy 경고 해결

- 원인: Docker healthcheck가 `/healthz` 응답을 받지만 Python task runner 미설치 경고
- 실제 기능에는 영향 없으나, `docker compose ps`에서 unhealthy로 표시됨
- 선택지: (1) healthcheck 조건 완화 (2) Python 3 설치 (3) task runner 비활성화

### 3.3 [낮음] 12개월 무료 만료 대비

- AWS 프리티어 만료 전 예산 알림 설정 (월 $1 초과 시 이메일)
- 만료 후 대안: GCP e2-micro 영구 무료 이전 또는 Hetzner CX23 (3.49유로/월)
- Elastic IP 미할당 시 재부팅마다 IP 변경됨 — 현재 Cloudflare Tunnel이므로 큰 문제 아님

### 3.4 [낮음] 코드 커밋 + leanskills 동기화

- 로컬 변경사항 커밋 필요 (schedule.py, deploy-to-aws.sh)
- skill 코드는 `~/.claude/skills/beyondworks-assistant/`에도 동기화 필요
- leanskills 레포에도 반영 필요 (커밋 규칙에 따라)

---

## 4. 수정한 파일 상세

### `docker/assistant/domains/schedule.py`

| 라인 | 변경 | 설명 |
|------|------|------|
| 118-121 | 추가 | 시스템 프롬프트에 "완료 일정 포함 규칙" |
| 339-388 | 재작성 | `_briefing()` — morning/evening/daily/weekly 4모드 |
| 391-420 | 재작성 | `_reminder()` — thresholds 리스트 기반 4단계 |
| 426 | 수정 | `handle()` mode 분기에 morning/evening 추가 |
| 438-469 | 수정 | 컨텍스트에 오늘 일정 완료/미완료 사전 분류 |

### `docker/deploy-to-aws.sh` (신규)

- rsync로 assistant 코드 동기화
- scp로 Docker 설정 파일 동기화
- 기본: assistant 재시작 / `--rebuild`: 전체 재빌드

---

## 5. 잘한 점 (성공 패턴)

### 5.1 코드 방어 원칙 준수

완료 일정 누락 버그 수정에서 **프롬프트만으로 해결하지 않고 코드 방어를 병행**.
MEMORY.md 교훈 #11("AI 행동 제어는 프롬프트가 아닌 코드로")을 정확히 적용함.
- 프롬프트: "완료 항목도 반드시 포함" (힌트 역할)
- 코드: 오늘 일정을 미완료/완료로 사전 분류 + 헤더에 건수 명시 (보장 역할)

### 5.2 레거시 호환 유지

`daily_briefing`을 삭제하지 않고 `morning_briefing`과 동일하게 동작하도록 유지.
기존 n8n 워크플로우가 `daily_briefing` 모드로 호출 중일 수 있으므로, 깨뜨리지 않음.

### 5.3 배포 스크립트 자동화

수동 scp/ssh 대신 `deploy-to-aws.sh` 스크립트로 1커맨드 배포.
assistant만 재시작하는 기본 모드를 두어 빠른 반복 배포 가능 (n8n/cloudflared 재빌드 불필요).

### 5.4 조사 → 결정 → 실행 흐름

호스팅 옵션을 체계적으로 조사(research-analyst 에이전트 활용) → 사용자에게 정리된 비교표 제시 → 사용자 선택 후 즉시 가이드 작성. 불필요한 논의 없이 효율적으로 진행.

---

## 6. 못한 점 (개선 포인트)

### 6.1 n8n 워크플로우까지 완성하지 못함

브리핑/리마인더 코드를 작성했지만, 실제 n8n Cron 워크플로우를 만들지 않아서 **아직 자동으로 작동하지 않음**. 코드 완성 = 기능 완성이 아님. 다음 세션에서 반드시 워크플로우까지 만들어야 함.

### 6.2 E2E 테스트 미실행

schedule.py 변경 후 서버에 배포했지만, 실제 Slack에서 "오늘 일정 알려줘" 메시지를 보내서 완료 일정이 포함되는지 검증하지 않음. 배포 = 검증은 아님.

### 6.3 리마인더 ±1분 오차가 실용적인지 미검증

Cron이 1분 간격으로 호출한다고 가정했지만, 실제 n8n Cron의 실행 정확도(지연, 스킵 등)와 Python 코드 실행 시간을 합치면 ±1분 허용 오차가 너무 좁을 수 있음. 실제 운영 후 ±2분으로 늘려야 할 수도 있음.

### 6.4 가이드 문서의 경로 불일치

AWS 가이드에서 `~/n8n-docker` 경로를 사용했지만 실제 서버는 `~/n8n`. 이전 세션에서 이미 서버를 구성했기 때문. 가이드를 새 사용자 기준으로 작성한 것과 기존 서버의 상태가 다름.

### 6.5 커밋 없이 세션 종료

작업이 완료되었지만 git 커밋을 하지 않은 채 세션이 끝남. 다음 세션 시작 시 dirty 상태에서 시작하게 되어 혼란 가능.

---

## 7. 빠른 시작 (다음 세션용)

```bash
# 1. 현재 상태 확인
git status
git diff --stat

# 2. 서버 상태 확인
ssh -i ~/Downloads/n8n-key.pem ubuntu@54.180.68.210 "cd ~/n8n && docker compose ps"

# 3. 코드 변경 후 배포
/Users/yoogeon/n8n/docker/deploy-to-aws.sh          # assistant만 재시작
/Users/yoogeon/n8n/docker/deploy-to-aws.sh --rebuild # 전체 재빌드

# 4. 서버 로그 확인
ssh -i ~/Downloads/n8n-key.pem ubuntu@54.180.68.210 "cd ~/n8n && docker compose logs -f --tail=30"

# 5. 브리핑 테스트 (서버에서)
curl -s -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"domain":"schedule","mode":"morning_briefing"}' | python3 -m json.tool

# 6. 리마인더 테스트 (서버에서)
curl -s -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"domain":"schedule","mode":"reminder"}' | python3 -m json.tool
```

---

## 8. 관련 문서 링크

| 문서 | 경로 | 용도 |
|------|------|------|
| AWS 설치 가이드 | [aws-free-tier-setup-guide.md](aws-free-tier-setup-guide.md) | AWS 계정~Docker 설치 |
| 개발 계획 | [Develope.md](Develope.md) | 전체 기능 로드맵 |
| MCP 장애 포스트모템 | [2026-02-08-n8n-ssh-mcp-postmortem.md](2026-02-08-n8n-ssh-mcp-postmortem.md) | n8n MCP 교훈 |
| workspace 방어 코드 | [2026-02-09-workspace-create-record-fix.md](2026-02-09-workspace-create-record-fix.md) | 코드 방어 3층 패턴 |
| 할루시네이션 수정 | [hallucination-fix-analysis.md](hallucination-fix-analysis.md) | 감지 로직 스코프 |
