"""
환경 변수 및 설정 관리
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# api/.env 를 cwd와 무관하게 항상 로드 (uvicorn 실행 경로에 따라 .env 미발견 방지)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class Settings:
    """앱 설정 (환경변수 로드)."""

    def __init__(self) -> None:
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        self.supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
        # CosIng 크롤러 지연 설정 (초)
        self.cosing_search_delay_sec: float = float(os.getenv("COSING_SEARCH_DELAY_SEC", "4"))
        self.cosing_detail_delay_sec: float = float(os.getenv("COSING_DETAIL_DELAY_SEC", "2"))
        self.cosing_request_delay_sec: float = float(os.getenv("COSING_REQUEST_DELAY_SEC", "0.8"))
        self.cosing_headless: bool = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
        # CosIng 크롤 결과 CSV 저장 경로 (프로젝트 루트 기준)
        self.cosing_download_dir: str = os.getenv("COSING_DOWNLOAD_DIR", "cosing_downloads")
        # 올리브영 크롤러 설정
        self.olive_detail_delay_sec: float = float(os.getenv("OLIVE_DETAIL_DELAY_SEC", "2"))
        self.olive_request_delay_sec: float = float(os.getenv("OLIVE_REQUEST_DELAY_SEC", "1"))
        self.olive_download_dir: str = os.getenv("OLIVE_DOWNLOAD_DIR", "olive_downloads")
        self.olive_headless: bool = os.getenv("OLIVE_HEADLESS", "true").lower() in ("1", "true", "yes")


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤."""
    return Settings()
