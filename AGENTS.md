# AGENTS.md

This file provides guidance on how to work with the n8n repository.

## Project Overview

n8n is a workflow automation platform written in TypeScript, using a monorepo
structure managed by pnpm workspaces. It consists of a Node.js backend, Vue.js
frontend, and extensible node-based workflow engine.

## General Guidelines

- Always use pnpm
- We use Linear as a ticket tracking system
- We use Posthog for feature flags
- When starting to work on a new ticket – create a new branch from fresh
  master with the name specified in Linear ticket
- When creating a new branch for a ticket in Linear - use the branch name
  suggested by linear
- Use mermaid diagrams in MD files when you need to visualise something

## Essential Commands

### Building
Use `pnpm build` to build all packages. ALWAYS redirect the output of the
build command to a file:

```bash
pnpm build > build.log 2>&1
```

You can inspect the last few lines of the build log file to check for errors:
```bash
tail -n 20 build.log
```

### Testing
- `pnpm test` - Run all tests
- `pnpm test:affected` - Runs tests based on what has changed since the last
  commit

Running a particular test file requires going to the directory of that test
and running: `pnpm test <test-file>`.

When changing directories, use `pushd` to navigate into the directory and
`popd` to return to the previous directory. When in doubt, use `pwd` to check
your current directory.

### Code Quality
- `pnpm lint` - Lint code
- `pnpm typecheck` - Run type checks

Always run lint and typecheck before committing code to ensure quality.
Execute these commands from within the specific package directory you're
working on (e.g., `cd packages/cli && pnpm lint`). Run the full repository
check only when preparing the final PR. When your changes affect type
definitions, interfaces in `@n8n/api-types`, or cross-package dependencies,
build the system before running lint and typecheck.

## Architecture Overview

**Monorepo Structure:** pnpm workspaces with Turbo build orchestration

### Package Structure

The monorepo is organized into these key packages:

- **`packages/@n8n/api-types`**: Shared TypeScript interfaces between frontend and backend
- **`packages/workflow`**: Core workflow interfaces and types
- **`packages/core`**: Workflow execution engine
- **`packages/cli`**: Express server, REST API, and CLI commands
- **`packages/editor-ui`**: Vue 3 frontend application
- **`packages/@n8n/i18n`**: Internationalization for UI text
- **`packages/nodes-base`**: Built-in nodes for integrations
- **`packages/@n8n/nodes-langchain`**: AI/LangChain nodes
- **`@n8n/design-system`**: Vue component library for UI consistency
- **`@n8n/config`**: Centralized configuration management

## Technology Stack

- **Frontend:** Vue 3 + TypeScript + Vite + Pinia + Storybook UI Library
- **Backend:** Node.js + TypeScript + Express + TypeORM
- **Testing:** Jest (unit) + Playwright (E2E)
- **Database:** TypeORM with SQLite/PostgreSQL/MySQL support
- **Code Quality:** Biome (for formatting) + ESLint + lefthook git hooks

### Key Architectural Patterns

1. **Dependency Injection**: Uses `@n8n/di` for IoC container
2. **Controller-Service-Repository**: Backend follows MVC-like pattern
3. **Event-Driven**: Internal event bus for decoupled communication
4. **Context-Based Execution**: Different contexts for different node types
5. **State Management**: Frontend uses Pinia stores
6. **Design System**: Reusable components and design tokens are centralized in
   `@n8n/design-system`, where all pure Vue components should be placed to
   ensure consistency and reusability

## Key Development Patterns

- Each package has isolated build configuration and can be developed independently
- Hot reload works across the full stack during development
- Node development uses dedicated `node-dev` CLI tool
- Workflow tests are JSON-based for integration testing
- AI features have dedicated development workflow (`pnpm dev:ai`)

### TypeScript Best Practices
- **NEVER use `any` type** - use proper types or `unknown`
- **Avoid type casting with `as`** - use type guards or type predicates instead
- **Define shared interfaces in `@n8n/api-types`** package for FE/BE communication

### Error Handling
- Don't use `ApplicationError` class in CLI and nodes for throwing errors,
  because it's deprecated. Use `UnexpectedError`, `OperationalError` or
  `UserError` instead.
- Import from appropriate error classes in each package

### Frontend Development
- **All UI text must use i18n** - add translations to `@n8n/i18n` package
- **Use CSS variables directly** - never hardcode spacing as px values
- **data-test-id must be a single value** (no spaces or multiple values)

When implementing CSS, refer to @packages/frontend/CLAUDE.md for guidelines on
CSS variables and styling conventions.

### Testing Guidelines
- **Always work from within the package directory** when running tests
- **Mock all external dependencies** in unit tests
- **Confirm test cases with user** before writing unit tests
- **Typecheck is critical before committing** - always run `pnpm typecheck`
- **When modifying pinia stores**, check for unused computed properties

What we use for testing and writing tests:
- For testing nodes and other backend components, we use Jest for unit tests. Examples can be found in `packages/nodes-base/nodes/**/*test*`.
- We use `nock` for server mocking
- For frontend we use `vitest`
- For E2E tests we use Playwright. Run with `pnpm --filter=n8n-playwright test:local`.
  See `packages/testing/playwright/README.md` for details.

### Common Development Tasks

When implementing features:
1. Define API types in `packages/@n8n/api-types`
2. Implement backend logic in `packages/cli` module, follow
   `@packages/cli/scripts/backend-module/backend-module-guide.md`
3. Add API endpoints via controllers
4. Update frontend in `packages/editor-ui` with i18n support
5. Write tests with proper mocks
6. Run `pnpm typecheck` to verify types

## Github Guidelines
- When creating a PR, use the conventions in
  `.github/pull_request_template.md` and
  `.github/pull_request_title_conventions.md`.
- Use `gh pr create --draft` to create draft PRs.
- Always reference the Linear ticket in the PR description,
  use `https://linear.app/n8n/issue/[TICKET-ID]`
- always link to the github issue if mentioned in the linear ticket.

---

## Custom Deployment Guide (Beyondworks)

이 섹션은 n8n 커스텀 배포에 대한 가이드라인이다.
워크플로우, 스킬, 참조 문서는 [beyondworks/leanskills](https://github.com/beyondworks/leanskills) 레포에서 관리한다.

### 레포 분리 규칙

| 항목 | 레포 | 이유 |
|------|------|------|
| n8n 코어 패키지, i18n | **n8n** | 인스턴스 소프트웨어 |
| Docker 배포 (Dockerfile, compose, scripts) | **n8n** | 인스턴스 배포 설정 |
| CLAUDE.md, AGENTS.md | **n8n** | 프로젝트 가이드 |
| 워크플로우 JSON | **leanskills** | `workflows/` |
| Claude Code 스킬 (Python) | **leanskills** | `skills/` |
| n8n 노드 참조 문서 | **leanskills** | `n8n-reference/` |
| 배포 스크립트 (deploy.sh 등) | **leanskills** | `workflows/scripts/` |

### Docker 배포

- **베이스 이미지**: `docker.n8n.io/n8nio/n8n:latest`
- **시간대**: 항상 `GENERIC_TIMEZONE=Asia/Seoul` + `TZ=Asia/Seoul` 설정
- **볼륨**: `~/.n8n:/home/node/.n8n` (로컬 데이터 유지)
- **포트**: 5678 (기본)
- **터널**: `N8N_TUNNEL_MODE=true` (외부 접속 기본 활성화)

### API 키 관리

- 모든 API 키는 환경 변수로 관리 (하드코딩 금지)
- Docker: `.env` 파일 사용 (`.env.example`을 복사)
- Python 스킬: `notion_config.local.json` (로컬 오버라이드, git 미추적)
- `notion_config.json`에는 API 키를 절대 포함하지 않는다

### 스크립트 작성 규칙

- Bash 스크립트: Mac/Linux용 `.sh` + Windows용 `.bat` 양쪽 제공
- Python 스크립트: 타입 힌트 사용, `if __name__ == "__main__"` 패턴
- 모든 스크립트는 `chmod +x`로 실행 권한 부여
- 한국어 주석 허용 (사용자 대상이 한국어 사용자)
