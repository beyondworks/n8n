![Banner image](https://user-images.githubusercontent.com/10284570/173569848-c624317f-42b1-45a6-ab09-f0ea3c247648.png)

# n8n - 워크플로우 자동화 플랫폼

> 🇰🇷 **한국어** | [English](#english)

n8n은 코드의 유연성과 노코드의 빠른 속도를 동시에 제공하는 워크플로우 자동화 플랫폼입니다. 400개 이상의 통합, 네이티브 AI 기능, fair-code 라이선스를 통해 데이터와 배포를 완벽히 제어하면서 강력한 자동화를 구축할 수 있습니다.

![n8n.io - Screenshot](https://raw.githubusercontent.com/n8n-io/n8n/master/assets/n8n-screenshot-readme.png)

---

## 🚀 빠른 시작 (Docker)

**초보자도 10분 안에 설치 가능!**

### 1단계: Docker 설치
- **Mac**: [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 다운로드
- **Windows**: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드

### 2단계: 프로젝트 다운로드
```bash
git clone https://github.com/beyondworks/n8n.git
cd n8n/docker
```

### 3단계: 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 API 키 입력
```

### 4단계: 실행
```bash
docker-compose up -d
```

### 5단계: 접속
브라우저에서 **http://localhost:5678** 접속

🎉 **끝!**

> 📖 **상세 가이드**: [docker/README.md](./docker/README.md)에서 API 키 발급 방법, 문제 해결 등 자세한 내용을 확인하세요.

---

## 📦 포함된 워크플로우

### Daily News Clipping (뉴스 자동 클리핑)
- **기능**: 매일 아침 9시 자동으로 5개 카테고리 뉴스 수집
- **카테고리**: AI, Design, Branding, Build, Marketing
- **저장**: Notion 데이터베이스에 자동 저장
- **요약**: 한국어 요약, 핵심 내용, 키워드 추출

---

## 🔑 필요한 API 키

| API | 용도 | 발급 링크 |
|-----|------|----------|
| Perplexity | 뉴스 검색 | [perplexity.ai](https://www.perplexity.ai/) |
| Notion | 데이터 저장 | [notion.so/my-integrations](https://www.notion.so/my-integrations) |
| OpenAI | AI 요약 (선택) | [platform.openai.com](https://platform.openai.com/) |

---

## 💻 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `docker-compose up -d` | 시작 |
| `docker-compose down` | 중지 |
| `docker-compose restart` | 재시작 |
| `docker-compose logs -f` | 로그 보기 |

---

## 🌟 주요 기능

- **코드가 필요할 때 코드 사용**: JavaScript/Python 작성, npm 패키지 추가, 또는 비주얼 인터페이스 사용
- **AI 네이티브 플랫폼**: LangChain 기반 AI 에이전트 워크플로우 구축
- **완전한 제어**: fair-code 라이선스로 셀프 호스팅 또는 [클라우드](https://app.n8n.cloud/login) 사용
- **엔터프라이즈 지원**: 고급 권한, SSO, 에어갭 배포

---

## 📚 리소스

- 📖 [공식 문서](https://docs.n8n.io)
- 🔧 [400+ 통합](https://n8n.io/integrations)
- 💡 [예제 워크플로우](https://n8n.io/workflows)
- 🤖 [AI & LangChain 가이드](https://docs.n8n.io/advanced-ai/)
- 👥 [커뮤니티 포럼](https://community.n8n.io)

---

## 📞 지원

도움이 필요하신가요?
- **GitHub Issues**: [이슈 등록](https://github.com/beyondworks/n8n/issues)
- **Email**: beyondworks.br@gmail.com

---

<br>

---

# English

n8n is a workflow automation platform that gives technical teams the flexibility of code with the speed of no-code. With 400+ integrations, native AI capabilities, and a fair-code license, n8n lets you build powerful automations while maintaining full control over your data and deployments.

## Quick Start (Docker)

```bash
git clone https://github.com/beyondworks/n8n.git
cd n8n/docker
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

Access at **http://localhost:5678**

> 📖 **Detailed Guide**: See [docker/README.md](./docker/README.md) for API key setup and troubleshooting.

## Key Capabilities

- **Code When You Need It**: Write JavaScript/Python, add npm packages, or use the visual interface
- **AI-Native Platform**: Build AI agent workflows based on LangChain with your own data and models
- **Full Control**: Self-host with our fair-code license or use our [cloud offering](https://app.n8n.cloud/login)
- **Enterprise-Ready**: Advanced permissions, SSO, and air-gapped deployments
- **Active Community**: 400+ integrations and 900+ ready-to-use [templates](https://n8n.io/workflows)

## Resources

- 📚 [Documentation](https://docs.n8n.io)
- 🔧 [400+ Integrations](https://n8n.io/integrations)
- 💡 [Example Workflows](https://n8n.io/workflows)
- 🤖 [AI & LangChain Guide](https://docs.n8n.io/advanced-ai/)
- 👥 [Community Forum](https://community.n8n.io)

## License

n8n is [fair-code](https://faircode.io) distributed under the [Sustainable Use License](https://github.com/n8n-io/n8n/blob/master/LICENSE.md) and [n8n Enterprise License](https://github.com/n8n-io/n8n/blob/master/LICENSE_EE.md).

---

Made with ❤️ by Beyondworks | Based on [n8n](https://github.com/n8n-io/n8n)
