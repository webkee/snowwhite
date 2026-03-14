"""
KCA 성분사전 HTTP 크롤러
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.crawlers.parsers import parse_detail_page, parse_list_page
from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)

LIST_URL = "https://kcia.or.kr/cid/search/ingd_list.php"
DETAIL_URL = "https://kcia.or.kr/cid/search/ingd_view.php"
CONCURRENT_REQUESTS = 15
BATCH_UPDATE_INTERVAL = 50
MAX_RETRIES = 3
REQUEST_DELAY = 0.15  # 초 (서버 부하 완화)


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str:
    """
    HTTP GET with retries.

    response.content를 명시적으로 UTF-8로 디코딩합니다.
    r.text 접근 시 내부 인코딩 감지가 requests.Response.apparent_encoding을
    기대하여 에러가 발생할 수 있으므로, content 기반 디코딩으로 회피합니다.
    """
    last_err: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            r = await client.get(url, timeout=30.0)
            r.raise_for_status()
            # r.text 대신 content를 명시적 디코딩 (apparent_encoding 의존 회피)
            raw = r.content
            charset = (
                r.headers.get("content-type", "")
                .split("charset=")[-1]
                .split(";")[0]
                .strip()
                .strip("'\"")
                or "utf-8"
            )
            try:
                return raw.decode(charset, errors="replace")
            except (LookupError, ValueError):
                return raw.decode("utf-8", errors="replace")
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1.0 * (attempt + 1))
    raise last_err or RuntimeError("fetch failed")


async def run_crawl(resume: bool = False) -> None:
    """
    KCA 성분사전 전체 크롤 실행.

    Args:
        resume: True면 마지막 처리 위치부터 이어받기
    """
    supabase = get_supabase()

    # crawl_state 업데이트 헬퍼
    def update_state(
        status: str,
        *,
        total_count: Optional[int] = None,
        processed_count: Optional[int] = None,
        last_ingredient_code: Optional[str] = None,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
        abort_requested: Optional[bool] = None,
    ) -> None:
        data: dict = {"status": status}
        if total_count is not None:
            data["total_count"] = total_count
        if processed_count is not None:
            data["processed_count"] = processed_count
        if last_ingredient_code is not None:
            data["last_ingredient_code"] = last_ingredient_code
        if error_message is not None:
            data["error_message"] = error_message
        if started_at is not None:
            data["started_at"] = started_at.isoformat()
        if ended_at is not None:
            data["ended_at"] = ended_at.isoformat()
        if abort_requested is not None:
            data["abort_requested"] = abort_requested
        supabase.table("crawl_state").upsert(
            {"source": "kcia", **data},
            on_conflict="source",
        ).execute()

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; KciaCrawler/1.0)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }

    def check_abort_requested() -> bool:
        """crawl_state의 abort_requested 플래그 확인."""
        row = (
            supabase.table("crawl_state")
            .select("abort_requested")
            .eq("source", "kcia")
            .limit(1)
            .execute()
        )
        first = (row.data or [{}])[0] if row.data else {}
        return bool(first.get("abort_requested"))

    try:
        now = datetime.now(timezone.utc)
        update_state(
            "running",
            total_count=0,
            processed_count=0,
            started_at=now,
            abort_requested=False,
        )
        if not resume:
            update_state("running", last_ingredient_code=None)

        last_code: Optional[str] = None
        if resume:
            row = (
                supabase.table("crawl_state")
                .select("last_ingredient_code")
                .eq("source", "kcia")
                .maybe_single()
                .execute()
            )
            if row.data and row.data.get("last_ingredient_code"):
                last_code = row.data["last_ingredient_code"]

        # 1) 리스트 페이지 순회하여 모든 성분코드 수집
        all_ids: list[str] = []
        page = 1
        total_from_site: Optional[int] = None

        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            while True:
                if check_abort_requested():
                    logger.info("크롤 중단 요청으로 인해 리스트 수집을 중단합니다.")
                    update_state(
                        "aborted",
                        processed_count=0,
                        ended_at=datetime.now(timezone.utc),
                    )
                    return

                url = f"{LIST_URL}?skind=ALL&sword=&sword2=&page={page}"
                await asyncio.sleep(REQUEST_DELAY)
                html = await _fetch_text(client, url)
                ids, total = parse_list_page(html)
                if total is not None:
                    total_from_site = total
                if not ids:
                    break
                for no in ids:
                    all_ids.append(no)
                if len(ids) < 10:  # 마지막 페이지
                    break
                page += 1

        # 이어받기: last_code 이후만 처리
        if last_code and last_code in all_ids:
            idx = all_ids.index(last_code)
            all_ids = all_ids[idx + 1 :]
        elif last_code:
            # last_code가 목록에 없으면 전체 재처리하지 않고 빈 목록으로
            all_ids = []

        total_to_process = len(all_ids)
        update_state("running", total_count=total_to_process or (total_from_site or 0))
        if total_to_process == 0:
            update_state("success", processed_count=0, ended_at=datetime.now(timezone.utc))
            return

        # 2) 상세 페이지 병렬 수집 및 DB 저장
        sem = asyncio.Semaphore(CONCURRENT_REQUESTS)
        processed = 0

        async def fetch_and_save(c: httpx.AsyncClient, no: str) -> Optional[dict]:
            async with sem:
                await asyncio.sleep(REQUEST_DELAY)
                url = f"{DETAIL_URL}?no={no}"
                try:
                    html = await _fetch_text(c, url)
                    data = parse_detail_page(html, no)
                    data["crawled_at"] = datetime.now(timezone.utc).isoformat()
                    supabase.table("kcia_ingredients").upsert(
                        data,
                        on_conflict="ingredient_code",
                    ).execute()
                    return data
                except Exception as e:
                    logger.warning("Failed to fetch no=%s: %s", no, e)
                    return None

        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as detail_client:
            for i in range(0, len(all_ids), CONCURRENT_REQUESTS * 2):
                if check_abort_requested():
                    logger.info("크롤 중단 요청으로 인해 추출을 종료합니다. (처리: %d/%d)", processed, total_to_process)
                    update_state(
                        "aborted",
                        processed_count=processed,
                        last_ingredient_code=last_code,
                        ended_at=datetime.now(timezone.utc),
                    )
                    return

                batch = all_ids[i : i + CONCURRENT_REQUESTS * 2]
                results = await asyncio.gather(
                    *[fetch_and_save(detail_client, no) for no in batch]
                )
                processed += sum(1 for r in results if r is not None)
                last_code = batch[-1] if batch else last_code
                update_state(
                    "running",
                    processed_count=processed,
                    last_ingredient_code=last_code,
                )
                if processed % BATCH_UPDATE_INTERVAL < len(batch):
                    logger.info("Progress: %d / %d", processed, total_to_process)

        update_state(
            "success",
            processed_count=processed,
            last_ingredient_code=all_ids[-1] if all_ids else last_code,
            ended_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.exception("Crawl failed: %s", e)
        update_state("error", error_message=str(e), ended_at=datetime.now(timezone.utc))
        raise
