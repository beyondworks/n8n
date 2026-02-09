# n8n (Beyondworks Custom Deployment)

공통 원칙/작업 방식은 로컬 글로벌 규칙인 `~/.claude/CLAUDE.md`를 따른다.

프로젝트 구현/배포 관련 세부 규칙은 `AGENTS.md`를 우선 참고한다.
장애/교훈 문서는 `claudedocs/2026-02-08-n8n-ssh-mcp-postmortem.md`를 참고한다.

n8n 워크플로우 자동화 플랫폼의 한국어 커스텀 배포 포크. Docker 기반 원클릭 배포를 제공한다.

워크플로우, 스킬, 참조 문서는 [beyondworks/leanskills](https://github.com/beyondworks/leanskills) 레포에서 관리한다.

@AGENTS.md

## 레포지토리 분리 구조

| 레포 | 내용 | 위치 |
|------|------|------|
| **n8n** (이 레포) | n8n 인스턴스 소프트웨어, Docker 배포, Korean i18n | `/Users/yoogeon/n8n` |
| **leanskills** | 워크플로우 JSON, Skills, n8n 참조 문서 | `/Users/yoogeon/leanskills` |

## 커스텀 프로젝트 구조

```
n8n/
├── docker/                          # Docker 배포 설정
│   ├── Dockerfile                   # 커스텀 n8n 이미지 (TZ=Asia/Seoul)
│   ├── docker-compose.yml           # 컨테이너 오케스트레이션
│   ├── .env.example                 # 환경 변수 템플릿
│   ├── start.sh / stop.sh / logs.sh # 원클릭 관리 스크립트
│   ├── start-with-tunnel.sh         # ngrok 터널링 (대안)
│   ├── tunnel-url.sh                # 터널 URL 확인
│   └── QUICK_START.md               # 빠른 시작 가이드
├── packages/                        # n8n 코어 패키지 (upstream)
└── .claude/
    └── settings.local.json          # Claude Code 권한 설정
```

**leanskills 레포** (`/Users/yoogeon/leanskills`):
```
leanskills/
├── skills/                          # Claude Code 스킬 (Python)
│   ├── content-repurposing/         # YouTube → Notion 파이프라인
│   ├── schedule-assistant/          # 스케줄 관리 어시스턴트
│   └── beyondworks-assistant/       # 멀티도메인 Notion 어시스턴트
├── workflows/                       # n8n 워크플로우 JSON
│   ├── schedule-assistant/          # 스케줄 어시스턴트 워크플로우
│   ├── beyondworks-assistant/       # Beyondworks 어시스턴트 워크플로우
│   └── scripts/                     # 배포 스크립트
└── n8n-reference/                   # n8n 노드/워크플로우 참조 문서
```

## 기술 스택 (Docker 배포)

- **컨테이너**: Docker + docker-compose
- **베이스 이미지**: `docker.n8n.io/n8nio/n8n:latest`
- **시간대**: Asia/Seoul (KST)
- **포트**: 5678
- **터널**: n8n 내장 터널 (기본 활성화)
- **데이터 저장소**: `~/.n8n` 볼륨 마운트

## API 연동

| 서비스 | 용도 | 환경변수 |
|--------|------|---------|
| Perplexity AI | 실시간 웹 검색 (뉴스) | `PERPLEXITY_API_KEY` |
| OpenAI GPT-4o | 콘텐츠 생성, 분류 | `OPENAI_API_KEY` |
| Notion | DB 저장, 콘텐츠 관리 | `NOTION_API_KEY` |
| Slack | 알림, AI 챗 | `SLACK_BOT_TOKEN` |
| Apify | YouTube 트랜스크립트 | `APIFY_API_TOKEN` |
| YouTube API | 비디오 메타데이터 | `YOUTUBE_API_KEY` |

## Docker 관리 명령

```bash
# 시작/중지
cd docker && ./start.sh      # 원클릭 시작 (Docker 체크, .env 생성, 컨테이너 정리 포함)
cd docker && ./stop.sh        # 정상 종료
cd docker && ./logs.sh        # 로그 확인

# 터널 (외부 접속)
cd docker && ./tunnel-url.sh  # 터널 URL 확인
cd docker && ./start-with-tunnel.sh  # ngrok 기반 터널
```

## MCP 서버 연동

### n8n-mcp
- **용도**: n8n 워크플로우 CRUD, 실행 관리
- **주요 도구**: `n8n_list_workflows`, `n8n_get_workflow`, `n8n_create_workflow`, `n8n_update_full_workflow`, `n8n_executions`
- **인증**: JWT API 키 (settings.local.json에 설정)
- **주의**: 정규식/백슬래시/따옴표 등 이스케이프에 민감한 n8n 표현식(특히 SSH 노드 커맨드)은 MCP로 수정하지 않는다. (참조: `claudedocs/2026-02-08-n8n-ssh-mcp-postmortem.md`)

### Notion MCP
- **용도**: Notion 검색, 블록/페이지 조회
- **주요 도구**: `API-post-search`, `API-get-block-children`

## 코딩 규칙

### Docker
- `.env.example`에 모든 환경 변수 문서화
- 시작/중지 스크립트는 Bash + Batch 양쪽 제공

### 커밋 분리 규칙
- **n8n 레포**: n8n 인스턴스 업데이트, Docker 배포 설정, Korean i18n만 커밋
- **leanskills 레포**: 워크플로우 JSON, Skills, 배포 스크립트, 참조 문서 커밋

---

## 실수 기록 (반복 금지)

<!--
형식:
### [날짜] 카테고리
**상황:** 무엇을 하려고 했는지
**실수:** 무엇이 잘못되었는지
**원인:** 왜 발생했는지
**해결:** 어떻게 수정했는지
**교훈:** 다음에 어떻게 해야 하는지
-->

### [2025-01] API 키 노출
**상황:** notion_config.json에 설정 저장
**실수:** API 키가 git에 커밋됨
**원인:** .gitignore에 로컬 설정 파일 미포함
**해결:** `security: remove API keys from notion_config.json` 커밋으로 제거
**교훈:** API 키는 반드시 환경변수 또는 `.local.json` 파일로 분리. `.local.json`은 .gitignore에 추가할 것

---

## 세션 학습 기록

### 2025-01 초기 설정 세션
**성공 패턴:**
- Docker 기반 원클릭 배포 구성 (start.sh → Docker 체크 → .env 생성 → 컨테이너 시작)
- n8n 내장 터널로 외부 접속 지원 (N8N_TUNNEL_MODE=true)
- 한국어 문서화 (README, QUICK_START.md)

### 2025-02 레포 분리 세션
**성공 패턴:**
- n8n 레포 (인스턴스 + Docker 배포) / leanskills 레포 (워크플로우 + 스킬) 분리
- .gitignore로 커스텀 파일 재추적 방지
- 심링크로 ~/.claude/skills/에서 leanskills 스킬 접근

**사용자 스타일:**
- 한국어 우선 문서화
- 원클릭 스크립트 선호 (복잡한 설정 최소화)
- n8n 워크플로우 JSON 기반 관리
