"""
성분 DB 조회 API 라우터

대한화장품협회 성분사전(kcia_ingredients) 및 CosIng(cosing_ingredients) 검색.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase_client import get_supabase

router = APIRouter()


def _sanitize_search_pattern(q: str) -> str:
    """
    검색어에서 PostgREST ilike 와일드카드(*) 제거하여 안전한 패턴 생성.
    패턴은 *keyword* 형태로 부분 일치 검색.
    """
    sanitized = q.strip().replace("*", "")
    return f"*{sanitized}*" if sanitized else ""


@router.get("/kcia/search")
async def search_kcia_ingredients(
    q: str = Query(..., min_length=1, description="검색어 (성분코드, 한글명, 영문명, CAS 번호)"),
    limit: int = Query(50, ge=1, le=100, description="최대 결과 수"),
) -> list[dict[str, Any]]:
    """
    대한화장품협회 성분사전 DB 검색.
    ingredient_code, ingredient_name, english_name, cas_number 컬럼에서 검색.
    """
    pattern = _sanitize_search_pattern(q)
    if not pattern or pattern == "**":
        return []

    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    or_filter = (
        f"ingredient_code.ilike.{pattern},"
        f"ingredient_name.ilike.{pattern},"
        f"english_name.ilike.{pattern},"
        f"cas_number.ilike.{pattern}"
    )
    result = (
        supabase.table("kcia_ingredients")
        .select("*")
        .or_(or_filter)
        .order("ingredient_code")
        .limit(limit)
        .execute()
    )
    return list(result.data or [])


@router.get("/cosing/search")
async def search_cosing_ingredients(
    q: str = Query(..., min_length=1, description="검색어 (INCI명, 설명, KCA 영문명, CAS 번호)"),
    limit: int = Query(50, ge=1, le=100, description="최대 결과 수"),
) -> list[dict[str, Any]]:
    """
    CosIng DB 검색.
    inci_name, description, kcia_english_name, cas_number 컬럼에서 검색.
    """
    pattern = _sanitize_search_pattern(q)
    if not pattern or pattern == "**":
        return []

    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    or_filter = (
        f"inci_name.ilike.{pattern},"
        f"description.ilike.{pattern},"
        f"kcia_english_name.ilike.{pattern},"
        f"cas_number.ilike.{pattern}"
    )
    result = (
        supabase.table("cosing_ingredients")
        .select("*")
        .or_(or_filter)
        .order("inci_name")
        .limit(limit)
        .execute()
    )
    return list(result.data or [])
