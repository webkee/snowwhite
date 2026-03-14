"""
크롤 및 내보내기 API 라우터
"""

import asyncio
import csv
import io
import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.crawlers.cosing import run_cosing_crawl
from app.crawlers.kcia import run_crawl
from app.crawlers.olive import run_olive_makeup_crawl, run_olive_skincare_crawl
from app.db.supabase_client import get_supabase

router = APIRouter()


def _run_crawl_background(resume: bool) -> None:
    """동기 래퍼 for BackgroundTasks."""
    asyncio.run(run_crawl(resume=resume))


def _run_cosing_crawl_background(resume: bool) -> None:
    """CosIng 크롤 동기 래퍼 for BackgroundTasks."""
    asyncio.run(run_cosing_crawl(resume=resume))


def _run_olive_crawl_background(
    categories: Optional[list[tuple[str, str]]] = None,
    max_products_per_category: Optional[int] = None,
) -> None:
    """올리브영 스킨케어 크롤 동기 래퍼 for BackgroundTasks."""
    asyncio.run(run_olive_skincare_crawl(
        categories=categories,
        max_products_per_category=max_products_per_category,
    ))


def _run_olive_makeup_crawl_background(
    categories: Optional[list[tuple[str, str]]] = None,
    max_products_per_category: Optional[int] = None,
) -> None:
    """올리브영 메이크업 크롤 동기 래퍼 for BackgroundTasks."""
    asyncio.run(run_olive_makeup_crawl(
        categories=categories,
        max_products_per_category=max_products_per_category,
    ))


@router.post("/kcia/start")
async def start_kcia_crawl(
    background_tasks: BackgroundTasks,
    resume: bool = False,
) -> dict[str, Any]:
    """
    KCA 성분 크롤 시작.
    resume=true 이면 마지막 처리 위치부터 이어받기.
    """
    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    # 이미 실행 중인지 확인 (maybe_single은 0행 시 204 에러 발생 → limit(1) 사용)
    row = (
        supabase.table("crawl_state")
        .select("status")
        .eq("source", "kcia")
        .limit(1)
        .execute()
    )
    first = (row.data or [{}])[0] if row.data else {}
    if first.get("status") == "running":
        raise HTTPException(
            status_code=409,
            detail="크롤이 이미 실행 중입니다.",
        )

    background_tasks.add_task(_run_crawl_background, resume)
    return {"status": "started", "resume": resume}


@router.post("/kcia/abort")
async def abort_kcia_crawl() -> dict[str, Any]:
    """
    실행 중인 KCA 성분 크롤에 중단 요청을 보냅니다.
    다음 배치 처리 전에 크롤러가 중단 요청을 확인하고 종료합니다.
    """
    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    row = (
        supabase.table("crawl_state")
        .select("status")
        .eq("source", "kcia")
        .limit(1)
        .execute()
    )
    first = (row.data or [{}])[0] if row.data else {}
    if first.get("status") != "running":
        raise HTTPException(
            status_code=409,
            detail="크롤이 실행 중이 아닙니다. 중단할 크롤이 없습니다.",
        )

    supabase.table("crawl_state").update(
        {"abort_requested": True}
    ).eq("source", "kcia").execute()

    return {"status": "abort_requested", "detail": "중단 요청이 전달되었습니다."}


@router.post("/kcia/reset")
async def reset_kcia_crawl_state() -> dict[str, Any]:
    """
    크롤 상태를 idle로 초기화 (에러로 중단된 running 상태 복구용).
    """
    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    supabase.table("crawl_state").upsert(
        {
            "source": "kcia",
            "status": "idle",
            "error_message": None,
            "ended_at": None,
            "abort_requested": False,
        },
        on_conflict="source",
    ).execute()
    return {"status": "reset", "detail": "크롤 상태가 초기화되었습니다."}


@router.get("/kcia/status")
async def get_kcia_status() -> dict[str, Any]:
    """KCA 크롤 진행 상태 조회."""
    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    row = (
        supabase.table("crawl_state")
        .select("*")
        .eq("source", "kcia")
        .limit(1)
        .execute()
    )
    first = (row.data or [{}])[0] if row.data else {}

    if not first:
        return {
            "status": "idle",
            "total_count": 0,
            "processed_count": 0,
            "last_ingredient_code": None,
            "error_message": None,
            "started_at": None,
            "ended_at": None,
        }

    return {
        "status": first.get("status", "idle"),
        "total_count": first.get("total_count", 0),
        "processed_count": first.get("processed_count", 0),
        "last_ingredient_code": first.get("last_ingredient_code"),
        "error_message": first.get("error_message"),
        "started_at": first.get("started_at"),
        "ended_at": first.get("ended_at"),
        "abort_requested": first.get("abort_requested", False),
    }


def _ingredients_to_records() -> list[dict[str, Any]]:
    """DB에서 성분 목록 조회하여 레코드 리스트 반환."""
    supabase = get_supabase()
    result = supabase.table("kcia_ingredients").select("*").order("ingredient_code").execute()
    return list(result.data or [])


@router.get("/kcia/export/json")
async def export_kcia_json() -> StreamingResponse:
    """KCA 성분 데이터 JSON 다운로드."""
    try:
        records = _ingredients_to_records()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    def iter_json() -> Any:
        yield json.dumps(records, ensure_ascii=False, indent=2)

    return StreamingResponse(
        iter_json(),
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=kcia-ingredients.json"
        },
    )


@router.get("/kcia/export/csv")
async def export_kcia_csv() -> StreamingResponse:
    """KCA 성분 데이터 CSV 다운로드."""
    try:
        records = _ingredients_to_records()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not records:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ingredient_code", "ingredient_name", "old_name", "english_name",
            "cas_number", "origin_definition", "blend_purpose", "source_url", "crawled_at"
        ])
        body = output.getvalue()
    else:
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=list(records[0].keys()),
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(records)
        body = output.getvalue()

    bom_body = "\ufeff" + body  # BOM for Excel UTF-8
    return StreamingResponse(
        iter([bom_body]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=kcia-ingredients.csv"
        },
    )


# --- CosIng ---


@router.post("/cosing/start")
async def start_cosing_crawl(
    background_tasks: BackgroundTasks,
    resume: bool = False,
) -> dict[str, Any]:
    """
    CosIng 크롤 시작.
    resume=true 이면 마지막 처리 위치부터 이어받기.
    """
    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    row = (
        supabase.table("crawl_state")
        .select("status")
        .eq("source", "cosing")
        .limit(1)
        .execute()
    )
    first = (row.data or [{}])[0] if row.data else {}
    if first.get("status") == "running":
        raise HTTPException(
            status_code=409,
            detail="크롤이 이미 실행 중입니다.",
        )

    background_tasks.add_task(_run_cosing_crawl_background, resume)
    return {"status": "started", "resume": resume}


@router.post("/cosing/abort")
async def abort_cosing_crawl() -> dict[str, Any]:
    """실행 중인 CosIng 크롤에 중단 요청."""
    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    row = (
        supabase.table("crawl_state")
        .select("status")
        .eq("source", "cosing")
        .limit(1)
        .execute()
    )
    first = (row.data or [{}])[0] if row.data else {}
    if first.get("status") != "running":
        raise HTTPException(
            status_code=409,
            detail="크롤이 실행 중이 아닙니다. 중단할 크롤이 없습니다.",
        )

    supabase.table("crawl_state").update(
        {"abort_requested": True}
    ).eq("source", "cosing").execute()

    return {"status": "abort_requested", "detail": "중단 요청이 전달되었습니다."}


@router.post("/cosing/reset")
async def reset_cosing_crawl_state() -> dict[str, Any]:
    """CosIng 크롤 상태를 idle로 초기화 (에러로 중단된 running 상태 복구용)."""
    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    supabase.table("crawl_state").upsert(
        {
            "source": "cosing",
            "status": "idle",
            "error_message": None,
            "ended_at": None,
            "abort_requested": False,
        },
        on_conflict="source",
    ).execute()
    return {"status": "reset", "detail": "크롤 상태가 초기화되었습니다."}


@router.get("/cosing/status")
async def get_cosing_status() -> dict[str, Any]:
    """CosIng 크롤 진행 상태 조회."""
    try:
        supabase = get_supabase()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    row = (
        supabase.table("crawl_state")
        .select("*")
        .eq("source", "cosing")
        .limit(1)
        .execute()
    )
    first = (row.data or [{}])[0] if row.data else {}

    if not first:
        return {
            "status": "idle",
            "total_count": 0,
            "processed_count": 0,
            "last_ingredient_code": None,
            "current_search_keyword": None,
            "current_search_result_count": None,
            "error_message": None,
            "started_at": None,
            "ended_at": None,
        }

    return {
        "status": first.get("status", "idle"),
        "total_count": first.get("total_count", 0),
        "processed_count": first.get("processed_count", 0),
        "last_ingredient_code": first.get("last_ingredient_code"),
        "current_search_keyword": first.get("current_search_keyword"),
        "current_search_result_count": first.get("current_search_result_count"),
        "error_message": first.get("error_message"),
        "started_at": first.get("started_at"),
        "ended_at": first.get("ended_at"),
        "abort_requested": first.get("abort_requested", False),
    }


def _cosing_ingredients_to_records() -> list[dict[str, Any]]:
    """cosing_ingredients 테이블에서 레코드 조회."""
    supabase = get_supabase()
    result = supabase.table("cosing_ingredients").select("*").order("inci_name").execute()
    return list(result.data or [])


@router.get("/cosing/export/json")
async def export_cosing_json() -> StreamingResponse:
    """CosIng 성분 데이터 JSON 다운로드."""
    try:
        records = _cosing_ingredients_to_records()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    def iter_json() -> Any:
        yield json.dumps(records, ensure_ascii=False, indent=2)

    return StreamingResponse(
        iter_json(),
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=cosing-ingredients.json"
        },
    )


@router.get("/cosing/export/csv")
async def export_cosing_csv() -> StreamingResponse:
    """CosIng 성분 데이터 CSV 다운로드."""
    try:
        records = _cosing_ingredients_to_records()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not records:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "inci_name", "description", "cas_number", "ec_number",
            "identified_ingredients", "cosmetics_regulation_provisions",
            "functions", "sccs_opinions", "kcia_english_name",
            "source_url", "crawled_at",
        ])
        body = output.getvalue()
    else:
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=list(records[0].keys()),
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(records)
        body = output.getvalue()

    bom_body = "\ufeff" + body  # BOM for Excel UTF-8
    return StreamingResponse(
        iter([bom_body]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=cosing-ingredients.csv"
        },
    )


# --- Olive Young 스킨케어 ---


@router.post("/olive/start")
async def start_olive_crawl(
    background_tasks: BackgroundTasks,
    max_products_per_category: Optional[int] = None,
) -> dict[str, Any]:
    """
    올리브영 스킨케어 상품 크롤 시작.

    스킨/토너, 에센스/세럼/앰플, 크림, 로션, 미스트/오일 5개 카테고리 전체 수집.
    max_products_per_category로 카테고리당 상품 수 제한 가능 (테스트용).
    결과는 olive_downloads/olive_skincare_{timestamp}.csv에 저장됩니다.
    """
    background_tasks.add_task(
        _run_olive_crawl_background,
        categories=None,
        max_products_per_category=max_products_per_category,
    )
    return {
        "status": "started",
        "detail": "올리브영 스킨케어 크롤이 백그라운드에서 시작되었습니다. 결과는 olive_downloads 폴더에 CSV로 저장됩니다.",
        "max_products_per_category": max_products_per_category,
    }


@router.get("/olive/export/latest")
async def export_olive_latest_csv() -> StreamingResponse:
    """
    올리브영 크롤 결과 중 가장 최근 CSV 파일 다운로드.
    olive_downloads 폴더에서 olive_skincare_*.csv 파일 중 가장 최신 파일을 반환합니다.
    """
    settings = get_settings()
    download_dir = getattr(settings, "olive_download_dir", "olive_downloads")
    from pathlib import Path
    api_root = Path(__file__).resolve().parent.parent.parent
    out_dir = api_root.parent / download_dir
    if not out_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="olive_downloads 폴더가 없거나 크롤 결과가 없습니다.",
        )
    csv_files = sorted(out_dir.glob("olive_skincare_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not csv_files:
        raise HTTPException(
            status_code=404,
            detail="크롤 결과 CSV 파일이 없습니다.",
        )
    latest = csv_files[0]
    body = latest.read_text(encoding="utf-8-sig")
    return StreamingResponse(
        iter([body]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={latest.name}"
        },
    )


# --- Olive Young 메이크업 ---


@router.post("/olive-makeup/start")
async def start_olive_makeup_crawl(
    background_tasks: BackgroundTasks,
    max_products_per_category: Optional[int] = None,
) -> dict[str, Any]:
    """
    올리브영 메이크업 상품 크롤 시작.

    립메이크업, 베이스메이크업, 아이메이크업 카테고리 전체 수집.
    max_products_per_category로 카테고리당 상품 수 제한 가능 (테스트용).
    결과는 olive_downloads/olive_makeup_{timestamp}.csv에 저장됩니다.
    """
    background_tasks.add_task(
        _run_olive_makeup_crawl_background,
        categories=None,
        max_products_per_category=max_products_per_category,
    )
    return {
        "status": "started",
        "detail": "올리브영 메이크업 크롤이 백그라운드에서 시작되었습니다. 결과는 olive_downloads 폴더에 CSV로 저장됩니다.",
        "max_products_per_category": max_products_per_category,
    }


@router.get("/olive-makeup/export/latest")
async def export_olive_makeup_latest_csv() -> StreamingResponse:
    """
    올리브영 메이크업 크롤 결과 중 가장 최근 CSV 파일 다운로드.
    olive_downloads 폴더에서 olive_makeup_*.csv 파일 중 가장 최신 파일을 반환합니다.
    """
    settings = get_settings()
    download_dir = getattr(settings, "olive_download_dir", "olive_downloads")
    from pathlib import Path
    api_root = Path(__file__).resolve().parent.parent.parent
    out_dir = api_root.parent / download_dir
    if not out_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="olive_downloads 폴더가 없거나 크롤 결과가 없습니다.",
        )
    csv_files = sorted(out_dir.glob("olive_makeup_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not csv_files:
        raise HTTPException(
            status_code=404,
            detail="메이크업 크롤 결과 CSV 파일이 없습니다.",
        )
    latest = csv_files[0]
    body = latest.read_text(encoding="utf-8-sig")
    return StreamingResponse(
        iter([body]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={latest.name}"
        },
    )
