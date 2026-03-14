# GitHub + Vercel 배포 가이드

관리자 대시보드(cosmetic-admin)를 GitHub와 Vercel로 배포하는 방법입니다.

> **현재 상태**: Git 초기화 및 Initial commit 완료됨.  
> GitHub 저장소 생성 후 아래 1.2 단계부터 진행하세요.

## 사전 요약

| 구성요소 | 위치 | 배포 대상 |
|----------|------|-----------|
| 관리자 대시보드 | `cosmetic-admin/` | Vercel |
| FastAPI 백엔드 | `api/` | Railway / Render / Fly.io (별도) |
| 챗봇 (향후) | `cosmetic-chat/` | Vercel (별도 프로젝트) |

---

## 1단계: GitHub 저장소 설정

### 1.1 로컬 Git 초기화

```bash
cd /Users/igigi/cursor_ws/snowwhite
git init
git add .
git commit -m "Initial commit: cosmetic-admin dashboard"
git branch -M main
```

### 1.2 GitHub 원격 저장소 생성 및 푸시

1. [github.com](https://github.com) → **New repository** 생성
2. 저장소 이름 예: `snowwhite`
3. README, .gitignore는 추가하지 않음

```bash
# 방법 1: 직접 실행
git remote add origin https://github.com/YOUR_USERNAME/snowwhite.git
git push -u origin main

# 방법 2: 헬퍼 스크립트 (YOUR_USERNAME을 본인 것으로 교체)
./scripts/push-to-github.sh https://github.com/YOUR_USERNAME/snowwhite.git
```

`YOUR_USERNAME`을 본인 GitHub 사용자명으로 바꾸세요.

---

## 2단계: Vercel 배포

### 2.1 프로젝트 import

1. [vercel.com](https://vercel.com) → **Sign Up** (GitHub 로그인 권장)
2. **Add New** → **Project**
3. **Import** → `snowwhite` 저장소 선택

### 2.2 프로젝트 설정 (필수)

| 설정 항목 | 값 | 설명 |
|-----------|-----|------|
| **Root Directory** | `cosmetic-admin` | Next.js 앱 위치 지정 |
| **Framework Preset** | Next.js | 자동 감지 |
| **Build Command** | `next build` | 기본값 |
| **Output Directory** | (비워둠) | 기본값 |

### 2.3 환경 변수

**Settings** → **Environment Variables** 에 추가:

| Name | Value | Environments |
|------|-------|--------------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR_API_URL` | Production, Preview |

- **로컬 전용**: `http://localhost:8000`
- **프로덕션**: FastAPI 배포 URL (Railway, Render 등)

### 2.4 배포 실행

**Deploy** 클릭 → 완료 후 `https://xxx.vercel.app` 형태 URL 발급

---

## 3단계: 자동 배포 (CI/CD)

- `main` 브랜치에 push 시 → 자동 배포
- PR 생성 시 → Preview 배포 URL 발급

---

## 4단계: 백엔드 API 배포 (선택)

크롤러 등 API 기능을 쓰려면 FastAPI(`api/`)를 별도 서비스에 배포합니다.

| 플랫폼 | 난이도 | 비고 |
|--------|--------|------|
| Railway | 낮음 | Dockerfile 또는 `uvicorn` 직접 실행 |
| Render | 낮음 | Web Service, 무료 티어 |
| Fly.io | 중간 | `fly launch` 사용 |

배포 후:

1. Vercel 환경 변수 `NEXT_PUBLIC_API_URL`을 해당 API URL로 수정
2. API 서버에 `CORS_ORIGINS` (커스텀 도메인 사용 시) 설정  
   - `*.vercel.app` 도메인은 기본 허용됨

---

## Monorepo: 챗봇 + 관리자 2개 URL

챗봇 앱이 추가되면 **저장소는 하나**, **Vercel 프로젝트는 2개**로 운영합니다.

| Vercel 프로젝트 | Root Directory | 결과 URL |
|-----------------|----------------|----------|
| snowwhite-admin | `cosmetic-admin` | admin.xxx.vercel.app |
| snowwhite-chat | `cosmetic-chat` | chat.xxx.vercel.app |

동일한 GitHub 저장소를 import하고, Root Directory만 다르게 설정하면 됩니다.

---

## 체크리스트

- [ ] GitHub 저장소 생성 및 코드 푸시
- [ ] Vercel에서 `cosmetic-admin`을 Root Directory로 import
- [ ] `NEXT_PUBLIC_API_URL` 환경 변수 설정
- [ ] (선택) FastAPI 백엔드 배포 및 CORS 설정
- [ ] 배포 URL 접속 테스트
