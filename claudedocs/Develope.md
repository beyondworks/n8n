# n8n & AI Assistant Server Development Documentation

**작성일**: 2026-02-15
**최종 업데이트**: 2026-02-15 (세션 2)
**프로젝트**: AWS n8n Cloud Server Setup & AI Assistant Enhancement
**인수인계 문서**: [2026-02-15-session-handover.md](2026-02-15-session-handover.md)

---

## 1. 프로젝트 개요

AWS EC2 프리티어 인스턴스에 n8n 자동화 서버와 Python 기반 AI 비서를 구축하고,
Cloudflare Tunnel을 통해 안전한 외부 접속 환경을 구성.
Notion 일정 관리 기능을 고도화하여 정기 브리핑 및 상세 리마인드 기능을 구현.

---

## 2. 작업 완료 내역

### 2.1 서버 인프라 구축 (세션 1)
- **AWS EC2 (Ubuntu 24.04 LTS)**: 인스턴스 생성, 보안 그룹 설정 (SSH 22번 포트만 개방)
- **Swap 메모리 (4GB)** 설정으로 저사양 환경(RAM 914MB)에서의 안정성 확보
- **Docker & Docker Compose** 설치 완료

### 2.2 n8n 및 서비스 배포 (세션 1)
- **컨테이너 구성**: n8n + assistant (Python, Port 8080) + cloudflared
- **배포 자동화 스크립트 (`deploy-to-aws.sh`)**:
  - 로컬 코드 및 설정 파일 자동 동기화 (rsync + scp)
  - SSH `StrictHostKeyChecking=no` 옵션으로 비대화형 배포
  - Docker 권한 문제 해결 (UID/GID 1000:1000 매핑)

### 2.3 외부 접속 및 보안 (세션 1)
- **Cloudflare Zero Trust Tunnel**: 도메인 `n8n.leanbot.cloud` 연결
- 인바운드 포트 개방 없이 터널링, SSL 자동 적용

### 2.4 기능 검증 (세션 1)
- `test_schedule_query.py`로 Notion 일정 조회 정상 동작 확인
- `NOTION_API_KEY` 환경 변수 누락 문제 해결

### 2.5 완료된 일정 누락 버그 수정 (세션 2)
- **문제**: AI가 Completed:True 일정을 자의적으로 제외하여 "없다"고 답변
- **원인**: Notion API는 정상 반환, LLM이 완료 항목을 해석 과정에서 제외
- **수정 (프롬프트 + 코드 방어 2중)**:
  - 프롬프트: "완료 일정도 반드시 포함" 규칙 추가 (schedule.py:118-121)
  - 코드: 오늘 일정을 미완료/완료로 사전 분류 + 헤더에 건수 명시 (schedule.py:438-461)
- **설계 원칙**: MEMORY.md 교훈 #11 "AI 행동 제어는 프롬프트가 아닌 코드로" 적용

### 2.6 오전/오후 브리핑 모드 분리 (세션 2)
- `morning_briefing`: 어제 놓친 일 + 오늘 할 일 + 응원
- `evening_briefing`: 오늘 완료 회고/칭찬 + 미완료 + 내일 미리보기
- `daily_briefing`: 레거시 호환 유지 (= morning_briefing)
- 모든 브리핑에 `PLAIN_TEXT_RULE` 적용 (기존 누락 수정)

### 2.7 리마인더 시간대 세분화 (세션 2)
- 기존: 1시간/30분/10분 (허용 오차 ±10분)
- 변경: **3시간/1시간/30분/10분** 전, 허용 오차 **±1분**
- `thresholds` 리스트 기반으로 리팩토링하여 확장 용이

### 2.8 배포 스크립트 개선 + AWS 배포 (세션 2)
- `deploy-to-aws.sh` 재작성: rsync 기반, 기본/--rebuild 2모드
- 수정 코드 AWS 배포 완료, assistant healthy 확인

---

## 3. 현재 시스템 상태

| 항목 | 값 |
|------|-----|
| 서버 IP | `54.180.68.210` |
| SSH | `ssh -i ~/Downloads/n8n-key.pem ubuntu@54.180.68.210` |
| 서버 경로 | `~/n8n` |
| 에디터 | https://n8n.leanbot.cloud |
| assistant | healthy |
| n8n | 동작 정상 (unhealthy 표시는 Python task runner 경고) |
| cloudflared | Up |

---

## 4. 향후 작업 계획

### 4.1 [높음] n8n Cron 워크플로우 구성

브리핑/리마인더 코드는 완성되었으나, 자동 호출하는 n8n 워크플로우가 아직 없음.

| 워크플로우 | Cron | 요청 body | 비고 |
|-----------|------|-----------|------|
| 오전 브리핑 | 매일 09:00 | `{"domain":"schedule","mode":"morning_briefing"}` | Slack 전송 |
| 오후 브리핑 | 매일 21:00 | `{"domain":"schedule","mode":"evening_briefing"}` | Slack 전송 |
| 리마인더 | 매 1분 | `{"domain":"schedule","mode":"reminder"}` | `has_reminder:true`일 때만 |

### 4.2 [중간] E2E 검증

- Slack에서 "오늘 일정 알려줘" → 완료 일정 포함 확인
- 브리핑 API 응답 내용 검증
- 리마인더 허용 오차 ±1분 실용성 확인 (운영 후 ±2분 조정 가능)

### 4.3 [낮음] n8n unhealthy 경고 해결

- 원인: Python task runner 미설치
- 선택지: healthcheck 완화 / Python 3 설치 / task runner 비활성화

### 4.4 [낮음] Git 커밋 + leanskills 동기화

- 로컬 변경사항 커밋 (schedule.py, deploy-to-aws.sh)
- `~/.claude/skills/beyondworks-assistant/` 동기화
- leanskills 레포 반영

### 4.5 [낮음] 12개월 무료 만료 대비

- AWS 예산 알림 설정 (월 $1 초과 시 이메일)
- 만료 후 대안: GCP e2-micro 영구 무료 / Hetzner CX23 (3.49유로/월)

---

## 5. 주요 파일 및 경로

| 파일 | 경로 | 설명 |
|------|------|------|
| 배포 스크립트 | `docker/deploy-to-aws.sh` | 1커맨드 AWS 배포 |
| AI 비서 메인 | `docker/assistant/assistant.py` | 라우터, 도메인 분류 |
| HTTP 서버 | `docker/assistant/server.py` | /invoke, /health 엔드포인트 |
| 일정 도메인 | `docker/assistant/domains/schedule.py` | 브리핑, 리마인더, CRUD |
| 테스트 | `docker/assistant/test_schedule_query.py` | Notion 조회 검증 |
| AWS 가이드 | `claudedocs/aws-free-tier-setup-guide.md` | 초보자용 9단계 |
| 인수인계 | `claudedocs/2026-02-15-session-handover.md` | 세션 상세 기록 + 학습 |
