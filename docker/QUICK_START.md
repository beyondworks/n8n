# 🚀 n8n 5분 빠른 시작 가이드

> **초보자도 5분 안에 실행 가능!** 터널링이 기본 활성화되어 있어 어디서든 접속 가능합니다.

---

## 📦 1단계: Docker 설치 (한 번만)

### Mac
1. [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 다운로드
2. 다운로드된 파일 실행 → Applications로 드래그
3. Docker 실행 → 상단 메뉴바에 🐳 고래 아이콘 확인

### Windows
1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드
2. 설치 파일 실행 → "Use WSL 2" 체크
3. 재부팅 후 Docker Desktop 실행

---

## ▶️ 2단계: n8n 실행

### Mac/Linux (터미널에서)
```bash
cd n8n/docker
./start.sh
```

### Windows (명령 프롬프트에서)
```bash
cd n8n\docker
start.bat
```

---

## 🌐 3단계: 접속하기

### 로컬 접속 (같은 컴퓨터)
```
http://localhost:5678
```

### 외부 접속 (다른 기기/네트워크)
터미널에서 터널 URL 확인:
```bash
./tunnel-url.sh
```

**예시 URL:**
```
https://abc123xyz.hooks.n8n.cloud
```

이 URL로 어디서든 접속 가능합니다:
- ✅ 스마트폰에서 접속
- ✅ 다른 컴퓨터에서 접속
- ✅ 외부 서비스에서 Webhook 수신

---

## 📋 자주 쓰는 명령어

| 명령어 | 설명 |
|--------|------|
| `./start.sh` | n8n 시작 |
| `./stop.sh` | n8n 중지 |
| `./logs.sh` | 로그 보기 |
| `./tunnel-url.sh` | 외부 접속 URL 확인 |

---

## ❓ 문제 해결

### "Docker가 실행되지 않았습니다" 오류
→ Docker Desktop을 먼저 실행하세요

### 터널 URL이 안 보여요
→ 약 30초 정도 기다린 후 `./tunnel-url.sh` 다시 실행

### 웹훅이 작동하지 않아요
→ 터널 URL을 웹훅 주소로 사용하세요

---

## 🔒 보안 설정 (선택)

외부에 공개할 때 비밀번호 설정을 권장합니다:

1. `.env` 파일 열기:
   ```bash
   nano .env  # 또는: open -e .env (Mac)
   ```

2. 다음 값 수정:
   ```
   N8N_BASIC_AUTH_ACTIVE=true
   N8N_BASIC_AUTH_USER=admin
   N8N_BASIC_AUTH_PASSWORD=원하는_비밀번호
   ```

3. n8n 재시작:
   ```bash
   ./stop.sh && ./start.sh
   ```

---

## 💡 알아두면 좋은 것

- **시간대**: 한국 시간(KST)으로 자동 설정됩니다
- **데이터 보존**: Docker를 중지해도 워크플로우는 저장됩니다
- **자동 재시작**: 컴퓨터 재부팅 후에도 자동으로 시작됩니다

---

**🎉 이제 n8n을 사용할 준비가 되었습니다!**

문의: [GitHub Issues](https://github.com/beyondworks/n8n/issues)
