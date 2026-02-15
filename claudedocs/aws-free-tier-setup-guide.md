# AWS 무료 서버에 n8n 올리기 (초보자 가이드)

> 목표: PC를 꺼도 n8n이 24시간 돌아가게 하기
> 비용: 12개월 무료 (이후 ~$9/월)
> 소요 시간: 약 30~40분

---

## 전체 흐름 (큰 그림)

```
1. AWS 계정 만들기 (5분)
2. 서버(EC2) 만들기 (10분)
3. 서버에 접속하기 (5분)
4. Docker 설치하기 (5분)
5. n8n 파일 올리기 (5분)
6. n8n 실행하기 (5분)
7. 잘 되는지 확인하기 (5분)
```

---

## 1단계: AWS 계정 만들기

### 1-1. AWS 가입 페이지 열기

- 브라우저에서 https://aws.amazon.com/free 접속
- **"무료 계정 생성"** (또는 "Create a Free Account") 클릭

### 1-2. 이메일 + 비밀번호 입력

- 이메일 주소 입력
- AWS 계정 이름 입력 (아무거나 OK, 예: "beyondworks")
- 이메일로 온 인증 코드 입력

### 1-3. 연락처 정보 입력

- 계정 유형: **개인** 선택
- 이름, 주소, 전화번호 입력 (한국 주소 OK)

### 1-4. 결제 정보 입력 (중요!)

- 신용카드/체크카드 번호 입력
- **카드가 있어야 가입 가능** (무료 티어 사용 시 과금 안 됨)
- 가입 시 $1 임시 결제 후 환불됨 (카드 유효성 확인용)

### 1-5. 본인 확인

- 전화번호 입력 → SMS 또는 음성 통화로 인증 코드 받기

### 1-6. 지원 플랜 선택

- **"기본 지원 - 무료"** 선택 (Basic Support - Free)

### 1-7. 완료!

- 계정 활성화까지 몇 분~24시간 걸릴 수 있음
- 보통 몇 분 이내에 활성화됨

---

## 2단계: 서버(EC2 인스턴스) 만들기

### 2-1. AWS 콘솔 접속

- https://console.aws.amazon.com 접속 후 로그인
- 상단 검색창에 **"EC2"** 입력 → EC2 대시보드 클릭

### 2-2. 리전(지역) 선택

- 우측 상단에 리전이 표시됨
- **"아시아 태평양 (서울) ap-northeast-2"** 선택
  - (서울이 없으면 도쿄 ap-northeast-1도 OK)

### 2-3. 인스턴스 시작

- **"인스턴스 시작"** (Launch Instance) 버튼 클릭

### 2-4. 이름 짓기

- 이름: **n8n-server** (아무거나 OK)

### 2-5. OS 선택

- **Ubuntu** 선택 (주황색 아이콘)
- 버전: **Ubuntu Server 24.04 LTS** (기본값 그대로)
- 아키텍처: **64비트 (x86)** (기본값 그대로)
- "프리 티어 사용 가능" 라벨이 있는지 확인!

### 2-6. 인스턴스 유형 선택

- **t2.micro** 선택 (기본값)
- "프리 티어 사용 가능" 라벨 확인!
- 스펙: 1 vCPU, 1 GB 메모리

### 2-7. 키 페어(비밀 열쇠) 만들기 ★★★ 매우 중요

키 페어 = 서버에 접속할 때 쓰는 비밀 열쇠 파일

- **"새 키 페어 생성"** 클릭
- 키 페어 이름: **n8n-key**
- 키 페어 유형: **RSA**
- 프라이빗 키 파일 형식: **.pem** 선택
- **"키 페어 생성"** 클릭 → `n8n-key.pem` 파일이 다운로드됨

> !! 이 파일은 딱 한 번만 다운로드됨. 절대 잃어버리면 안 됨 !!
> 다운로드 폴더에서 안전한 곳으로 옮겨두기

### 2-8. 네트워크(방화벽) 설정

- **"보안 그룹 생성"** 선택 (기본값)
- 체크박스 3개 모두 체크:
  - [x] SSH 트래픽 허용 (서버 접속용)
  - [x] HTTPS 트래픽 허용
  - [x] HTTP 트래픽 허용
- SSH 소스: **"내 IP"** 선택 (보안상 권장) 또는 **"위치 무관 0.0.0.0/0"**

### 2-9. 스토리지(저장 공간) 설정

- 기본 8 GiB → **30 GiB**로 변경 (무료 티어 한도)
- 볼륨 유형: **gp3** (기본값)

### 2-10. 보안 그룹에 포트 추가

"고급 세부 정보" 아래 **보안 그룹 규칙 편집**에서:

| 유형 | 포트 | 소스 | 용도 |
|------|------|------|------|
| SSH | 22 | 내 IP | 서버 접속 |
| HTTP | 80 | 0.0.0.0/0 | 웹 접속 |
| HTTPS | 443 | 0.0.0.0/0 | 보안 웹 접속 |
| 사용자 지정 TCP | 5678 | 0.0.0.0/0 | n8n 웹 에디터 |

> Cloudflare Tunnel을 쓰면 5678 포트는 안 열어도 되지만,
> 초기 설정/디버깅 시 열어두면 편함

### 2-11. 인스턴스 시작!

- **"인스턴스 시작"** 클릭
- 초록색 성공 메시지가 뜨면 완료!
- "인스턴스 보기" 클릭

### 2-12. 퍼블릭 IP 확인

- 인스턴스 목록에서 방금 만든 **n8n-server** 클릭
- **"퍼블릭 IPv4 주소"** 를 메모 (예: `3.34.xxx.xxx`)
- 이 IP가 서버 주소

---

## 3단계: 서버에 접속하기 (SSH)

### Mac 터미널에서 접속

```bash
# 1. 키 파일 권한 설정 (최초 1회)
chmod 400 ~/Downloads/n8n-key.pem

# 2. 서버 접속 (IP를 본인 서버 IP로 변경!)
ssh -i ~/Downloads/n8n-key.pem ubuntu@서버IP주소
```

예시:
```bash
ssh -i ~/Downloads/n8n-key.pem ubuntu@3.34.123.45
```

- "Are you sure you want to continue connecting?" 질문에 **yes** 입력
- `ubuntu@ip-xxx:~$` 프롬프트가 뜨면 접속 성공!

---

## 4단계: Docker 설치하기

서버에 접속한 상태에서 아래 명령어를 **한 줄씩** 복사해서 붙여넣기:

### 4-1. 시스템 업데이트

```bash
sudo apt update && sudo apt upgrade -y
```
(1~2분 소요)

### 4-2. Docker 설치

```bash
curl -fsSL https://get.docker.com | sudo sh
```
(1~2분 소요)

### 4-3. Docker를 sudo 없이 쓸 수 있게 설정

```bash
sudo usermod -aG docker ubuntu
```

### 4-4. 재접속 (권한 적용)

```bash
exit
```
그리고 다시 SSH 접속:
```bash
ssh -i ~/Downloads/n8n-key.pem ubuntu@서버IP주소
```

### 4-5. Docker 작동 확인

```bash
docker --version
docker compose version
```
버전 번호가 뜨면 성공!

### 4-6. Swap 메모리 설정 (★ 필수)

t2.micro는 RAM이 1GB뿐이라 Swap(가상 메모리)을 만들어야 함:

```bash
# 2GB 스왑 파일 생성
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 재부팅해도 유지되게 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 확인
free -h
```
Swap 항목에 2.0G가 뜨면 성공!

---

## 5단계: n8n 파일 올리기

### 5-1. 프로젝트 폴더 만들기 (서버에서)

```bash
mkdir -p ~/n8n-docker/assistant
```

### 5-2. 파일 업로드 (Mac 터미널에서 - 새 터미널 탭)

Mac에서 새 터미널을 열고 (서버 접속 아닌 로컬):

```bash
# docker-compose.yml 업로드
scp -i ~/Downloads/n8n-key.pem \
  /Users/yoogeon/n8n/docker/docker-compose.yml \
  ubuntu@서버IP:~/n8n-docker/

# Dockerfile 업로드
scp -i ~/Downloads/n8n-key.pem \
  /Users/yoogeon/n8n/docker/Dockerfile \
  ubuntu@서버IP:~/n8n-docker/

# entrypoint.sh 업로드
scp -i ~/Downloads/n8n-key.pem \
  /Users/yoogeon/n8n/docker/entrypoint.sh \
  ubuntu@서버IP:~/n8n-docker/

# .env 파일 업로드
scp -i ~/Downloads/n8n-key.pem \
  /Users/yoogeon/n8n/docker/.env \
  ubuntu@서버IP:~/n8n-docker/

# assistant 폴더 전체 업로드
scp -i ~/Downloads/n8n-key.pem -r \
  /Users/yoogeon/n8n/docker/assistant/ \
  ubuntu@서버IP:~/n8n-docker/assistant/
```

### 5-3. Cloudflare Tunnel 설정 복사 (이미 사용 중이라면)

```bash
# Mac 로컬의 cloudflared 설정을 서버로 복사
scp -i ~/Downloads/n8n-key.pem -r \
  ~/.cloudflared/ \
  ubuntu@서버IP:~/.cloudflared/
```

### 5-4. 파일 확인 (서버에서)

다시 서버 SSH 터미널로 돌아와서:

```bash
ls -la ~/n8n-docker/
```

이런 파일들이 보이면 성공:
```
docker-compose.yml
Dockerfile
entrypoint.sh
.env
assistant/
```

---

## 6단계: docker-compose.yml 수정 (서버 환경에 맞게)

### 6-1. 볼륨 경로 수정

서버에서 n8n 데이터 폴더 생성:

```bash
mkdir -p ~/.n8n
```

### 6-2. docker-compose.yml에서 volumes 확인

서버에서:
```bash
nano ~/n8n-docker/docker-compose.yml
```

volumes 부분이 이렇게 되어 있는지 확인:
```yaml
volumes:
  - ~/.n8n:/home/node/.n8n
```

- `Ctrl + X` → `Y` → `Enter` 로 저장하고 나오기

### 6-3. 기존 로컬 n8n 데이터 옮기기 (선택사항)

워크플로우/인증정보를 유지하고 싶으면 Mac에서:

```bash
# 로컬 n8n 데이터를 서버로 복사
scp -i ~/Downloads/n8n-key.pem -r \
  ~/.n8n/ \
  ubuntu@서버IP:~/.n8n/
```

> 이렇게 하면 기존 워크플로우, Credential(인증정보)이 모두 유지됨

---

## 7단계: n8n 실행하기!

### 7-1. 서버에서 Docker 빌드 + 실행

```bash
cd ~/n8n-docker
docker compose up -d --build
```

(첫 실행 시 이미지 다운로드 + 빌드로 3~5분 소요)

### 7-2. 상태 확인

```bash
docker compose ps
```

3개 서비스 모두 **Up** 또는 **healthy** 상태여야 함:
```
NAME          STATUS
n8n           Up (healthy)
assistant     Up (healthy)
cloudflared   Up
```

### 7-3. 로그 확인

```bash
docker compose logs -f --tail=50
```
(`Ctrl + C`로 로그 보기 종료)

에러가 있으면 로그에서 확인 가능.

### 7-4. 브라우저에서 확인

- **http://서버IP:5678** 접속
- n8n 에디터 화면이 뜨면 성공!
- Cloudflare Tunnel 사용 시 기존 도메인으로도 접속 확인

---

## 8단계: 자동 재시작 설정

서버가 재부팅되어도 Docker가 자동으로 시작되게 설정:

```bash
# Docker 서비스 자동 시작
sudo systemctl enable docker

# docker-compose도 자동 시작 (systemd 서비스 등록)
sudo tee /etc/systemd/system/n8n.service << 'EOF'
[Unit]
Description=n8n Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/n8n-docker
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable n8n
```

이제 서버가 재부팅되어도 n8n이 자동으로 시작됨!

---

## 9단계: 보안 설정 (권장)

### 9-1. n8n 비밀번호 설정

`.env` 파일 수정:
```bash
nano ~/n8n-docker/.env
```

아래 내용 추가/수정:
```
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=여기에_강력한_비밀번호_입력
```

저장 후 재시작:
```bash
cd ~/n8n-docker && docker compose up -d
```

### 9-2. 5678 포트 닫기 (Cloudflare Tunnel 사용 시)

Cloudflare Tunnel이 잘 작동하면 5678 포트를 닫아서 보안 강화:

- AWS 콘솔 → EC2 → 보안 그룹 → 인바운드 규칙 편집
- 5678 포트 규칙 삭제

---

## 자주 하는 작업 (치트시트)

```bash
# 서버 접속
ssh -i ~/Downloads/n8n-key.pem ubuntu@서버IP

# 상태 확인
cd ~/n8n-docker && docker compose ps

# 로그 보기
cd ~/n8n-docker && docker compose logs -f --tail=50

# 재시작
cd ~/n8n-docker && docker compose restart

# 중지
cd ~/n8n-docker && docker compose down

# 시작
cd ~/n8n-docker && docker compose up -d

# 코드 업데이트 후 재빌드
cd ~/n8n-docker && docker compose up -d --build

# 서버 메모리 확인
free -h

# 디스크 용량 확인
df -h
```

---

## 문제 해결

### "메모리 부족" (OOM Kill)

```bash
# 현재 메모리 사용량 확인
free -h
docker stats --no-stream

# swap이 켜져 있는지 확인
swapon --show
```

swap이 없으면 4-6단계를 다시 실행.

### "서버 접속 안 됨"

1. AWS 콘솔에서 인스턴스가 **Running** 상태인지 확인
2. 보안 그룹에서 SSH(22번 포트)가 열려 있는지 확인
3. 퍼블릭 IP가 바뀌었을 수 있음 (재부팅 시) → 탄력적 IP 할당 권장

### "퍼블릭 IP가 자꾸 바뀜"

탄력적 IP(Elastic IP) 할당:
- EC2 → 탄력적 IP → 탄력적 IP 주소 할당 → 인스턴스에 연결
- 무료 티어에서 인스턴스에 연결된 Elastic IP 1개는 무료
- **연결 안 하고 놀리면 과금됨** 주의!

### "Cloudflare Tunnel이 안 됨"

서버에서 cloudflared 설정 확인:
```bash
ls -la ~/.cloudflared/
# cert.pem, config.yml, <tunnel-id>.json 파일이 있어야 함
```

config.yml의 url이 `http://n8n:5678`인지 확인
(Docker 내부 네트워크에서는 컨테이너 이름으로 접근)

---

## 비용 주의사항

| 항목 | 무료 조건 |
|------|-----------|
| EC2 t2.micro | 12개월, 월 750시간 (1대 24/7 가능) |
| EBS 스토리지 | 30 GiB까지 |
| 데이터 전송 | 아웃바운드 월 15 GB |
| 탄력적 IP | 인스턴스에 연결된 1개만 무료 |

**12개월 후**: t2.micro ~$8.50/월 + 스토리지 ~$2.40/월 = **약 $11/월**

> 12개월 만료 전에 알림 설정 권장:
> AWS 콘솔 → 결제 → 예산 → 예산 생성 → 월 $1 초과 시 이메일 알림

---

## Mac에서 서버로 한 번에 배포하는 스크립트

아래 스크립트를 Mac에 저장하면 파일 업로드 + 재빌드를 한 번에 할 수 있음:

```bash
#!/bin/bash
# deploy-to-aws.sh
# 사용법: ./deploy-to-aws.sh

SERVER_IP="서버IP주소를여기에"
KEY_FILE="~/Downloads/n8n-key.pem"
REMOTE_DIR="~/n8n-docker"

echo "=== n8n AWS 배포 ==="

echo "[1/3] 파일 업로드..."
scp -i $KEY_FILE -r \
  /Users/yoogeon/n8n/docker/* \
  ubuntu@$SERVER_IP:$REMOTE_DIR/

echo "[2/3] 재빌드..."
ssh -i $KEY_FILE ubuntu@$SERVER_IP \
  "cd $REMOTE_DIR && docker compose up -d --build"

echo "[3/3] 상태 확인..."
ssh -i $KEY_FILE ubuntu@$SERVER_IP \
  "cd $REMOTE_DIR && docker compose ps"

echo "=== 배포 완료 ==="
```
