"""
Supabase 클라이언트
"""

from typing import Optional

from supabase import Client, create_client

from app.config import get_settings


def get_supabase() -> Client:
    """Supabase 클라이언트 반환."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise ValueError(
            "SUPABASE_URL 및 SUPABASE_SERVICE_ROLE_KEY 환경변수를 설정하세요."
        )
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
