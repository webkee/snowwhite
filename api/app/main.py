"""
FastAPI 앱 진입점
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import crawl, ingredients

app = FastAPI(
    title="KCA 성분 크롤러 API",
    description="대한화장품협회 성분사전 크롤링 및 내보내기 API",
    version="1.0.0",
)

# 개발/로컬 origin 허용: localhost, 127.0.0.1, LAN IP (172.16-31, 192.168, 10.x)
_CORS_ORIGIN_REGEX = (
    r"http://(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})"
    r"(:\d+)?$"
)
# Vercel 배포 도메인: *.vercel.app
_CORS_VERCEL_REGEX = r"https://[a-zA-Z0-9-]+\.vercel\.app$"

# CORS_ORIGINS env (쉼표 구분) - 프로덕션 커스텀 도메인용
_extra_origins = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", *_extra_origins],
    allow_origin_regex=f"({_CORS_ORIGIN_REGEX})|({_CORS_VERCEL_REGEX})",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crawl.router, prefix="/crawl", tags=["crawl"])
app.include_router(ingredients.router, prefix="/ingredients", tags=["ingredients"])


@app.get("/health")
async def health() -> dict[str, str]:
    """헬스 체크."""
    return {"status": "ok"}
