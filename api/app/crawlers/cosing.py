"""
CosIng 브라우저 크롤러 (Playwright)

kcia_ingredients.english_name으로 CosIng 검색 → 결과 링크 클릭 → 상세 파싱 → cosing_ingredients 저장 + CSV 다운로드 폴더 저장
"""

import csv
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.crawlers.cosing_parsers import parse_detail_page
from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)

COSING_BASE = "https://ec.europa.eu/growth/tools-databases/cosing/"
SOURCE = "cosing"

# CSV 저장용 컬럼 (cosing_ingredients 스키마 기준)
CSV_FIELDNAMES = [
    "cosing_id",
    "inci_name",
    "description",
    "cas_number",
    "ec_number",
    "identified_ingredients",
    "cosmetics_regulation_provisions",
    "functions",
    "sccs_opinions",
    "kcia_english_name",
    "source_url",
    "crawled_at",
]

# 크롤링 제외 링크 경로 (참조/도움말 등)
SKIP_HREF_PATTERNS = (
    "/reference/",
    "/advanced",
    "/user-manual",
    "/accessibility-statement",
    "europa.eu/info",
    "commission.europa.eu",
)


def _is_detail_link(href: str) -> bool:
    """상세 페이지 링크인지 판별 (참조/도움말 링크 제외)."""
    if not href or "cosing" not in href:
        return False
    href_lower = href.lower()
    return not any(p in href_lower for p in SKIP_HREF_PATTERNS)


async def run_cosing_crawl(resume: bool = False) -> None:
    """
    CosIng 크롤 실행.

    kcia_ingredients.english_name으로 검색 → 검색 결과의 INCI Name 링크 클릭 → 상세 파싱 → DB 저장.

    Args:
        resume: True면 last_ingredient_code(실제로는 last_english_name) 이후부터 이어받기
    """
    supabase = get_supabase()
    settings = get_settings()
    search_delay = settings.cosing_search_delay_sec
    detail_delay = settings.cosing_detail_delay_sec
    request_delay = settings.cosing_request_delay_sec
    headless = settings.cosing_headless

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
        current_search_keyword: Optional[str] = None,
        current_search_result_count: Optional[int] = None,
    ) -> None:
        data: dict = {"source": SOURCE, "status": status}
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
        if current_search_keyword is not None:
            # crawl_state.current_search_keyword가 varchar(50)인 경우 대비 절단
            data["current_search_keyword"] = current_search_keyword[:50] if len(current_search_keyword) > 50 else current_search_keyword
        if current_search_result_count is not None:
            data["current_search_result_count"] = current_search_result_count
        supabase.table("crawl_state").upsert(data, on_conflict="source").execute()

    def check_abort_requested() -> bool:
        row = (
            supabase.table("crawl_state")
            .select("abort_requested")
            .eq("source", SOURCE)
            .limit(1)
            .execute()
        )
        first = (row.data or [{}])[0] if row.data else {}
        return bool(first.get("abort_requested"))

    async def sleep_with_abort_check(seconds: float, interval: float = 0.5) -> bool:
        """
        sleep 중 abort_requested를 주기적으로 확인.
        Returns True if abort was requested (caller should exit), False otherwise.
        """
        elapsed = 0.0
        while elapsed < seconds:
            if check_abort_requested():
                return True
            chunk = min(interval, seconds - elapsed)
            await asyncio.sleep(chunk)
            elapsed += chunk
        return False

    try:
        # kcia_ingredients에서 english_name 조회 (NULL 제외, 중복 제거)
        result = (
            supabase.table("kcia_ingredients")
            .select("english_name")
            .not_.is_("english_name", "null")
            .not_.eq("english_name", "")
            .execute()
        )
        all_names: list[str] = []
        seen: set[str] = set()
        for row in (result.data or []):
            name = (row.get("english_name") or "").strip()
            if name and name not in seen:
                seen.add(name)
                all_names.append(name)

        if not all_names:
            update_state("success", processed_count=0, ended_at=datetime.now(timezone.utc))
            logger.info("kcia_ingredients에 english_name이 없습니다. 크롤을 종료합니다.")
            return

        # resume: last_ingredient_code 이후만 처리
        last_english_name: Optional[str] = None
        if resume:
            row = (
                supabase.table("crawl_state")
                .select("last_ingredient_code")
                .eq("source", SOURCE)
                .maybe_single()
                .execute()
            )
            if row.data and row.data.get("last_ingredient_code"):
                last_english_name = row.data["last_ingredient_code"]

        if last_english_name and last_english_name in all_names:
            idx = all_names.index(last_english_name)
            all_names = all_names[idx + 1:]
        elif last_english_name:
            all_names = []

        total_to_process = len(all_names)
        now = datetime.now(timezone.utc)
        update_state(
            "running",
            total_count=total_to_process,
            processed_count=0,
            started_at=now,
            abort_requested=False,
        )
        if not resume:
            update_state("running", last_ingredient_code=None)

        if total_to_process == 0:
            update_state("success", processed_count=0, ended_at=datetime.now(timezone.utc))
            return

        # CSV 다운로드 폴더 생성 및 파일 준비
        api_root = Path(__file__).resolve().parent.parent.parent
        workspace_root = api_root.parent
        download_dir = workspace_root / settings.cosing_download_dir
        download_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        csv_path = download_dir / f"cosing_ingredients_{timestamp}.csv"
        csv_file = open(csv_path, "w", newline="", encoding="utf-8-sig")  # utf-8-sig: Excel UTF-8 BOM
        csv_writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        csv_writer.writeheader()
        logger.info("CSV 저장 경로: %s", csv_path)

        if check_abort_requested():
            update_state(
                "aborted",
                processed_count=0,
                last_ingredient_code=None,
                ended_at=datetime.now(timezone.utc),
                abort_requested=False,
            )
            return

        from playwright.async_api import async_playwright

        processed_total = 0
        last_processed_name: Optional[str] = None

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless)
                try:
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        viewport={"width": 1280, "height": 720},
                    )
                    page = await context.new_page()

                    # 검색 페이지로 이동
                    if check_abort_requested():
                        update_state(
                            "aborted",
                            processed_count=0,
                            last_ingredient_code=None,
                            ended_at=datetime.now(timezone.utc),
                            abort_requested=False,
                        )
                        return
                    await page.goto(COSING_BASE, wait_until="domcontentloaded", timeout=30000)
                    if await sleep_with_abort_check(1.0):
                        update_state(
                            "aborted",
                            processed_count=0,
                            last_ingredient_code=None,
                            ended_at=datetime.now(timezone.utc),
                            abort_requested=False,
                        )
                        return

                    # 쿠키 동의 처리 (있을 경우)
                    try:
                        accept_btn = page.get_by_role("button", name="Accept all cookies").first
                        if await accept_btn.is_visible():
                            await accept_btn.click()
                            if await sleep_with_abort_check(0.5):
                                update_state(
                                    "aborted",
                                    processed_count=0,
                                    last_ingredient_code=None,
                                    ended_at=datetime.now(timezone.utc),
                                    abort_requested=False,
                                )
                                return
                    except Exception:
                        pass

                    for search_idx, english_name in enumerate(all_names):
                        if check_abort_requested():
                            logger.info("크롤 중단 요청으로 인해 종료합니다.")
                            update_state(
                                "aborted",
                                processed_count=processed_total,
                                last_ingredient_code=last_processed_name,
                                ended_at=datetime.now(timezone.utc),
                                abort_requested=False,
                            )
                            return

                        update_state(
                            "running",
                            processed_count=processed_total,
                            last_ingredient_code=last_processed_name,
                            current_search_keyword=english_name,
                            current_search_result_count=None,
                        )

                        try:
                            # Name 입력
                            keyword_input = page.locator("input#keyword").first
                            await keyword_input.fill("")
                            await asyncio.sleep(0.2)
                            await keyword_input.fill(english_name)
                            if await sleep_with_abort_check(request_delay):
                                update_state(
                                    "aborted",
                                    processed_count=processed_total,
                                    last_ingredient_code=last_processed_name,
                                    ended_at=datetime.now(timezone.utc),
                                    abort_requested=False,
                                )
                                return

                            # Search 클릭
                            search_btn = page.get_by_role("button", name="Search").first
                            await search_btn.click()
                            if await sleep_with_abort_check(search_delay):
                                update_state(
                                    "aborted",
                                    processed_count=processed_total,
                                    last_ingredient_code=last_processed_name,
                                    ended_at=datetime.now(timezone.utc),
                                    abort_requested=False,
                                )
                                return

                            # 결과 테이블의 INCI Name/Substance 링크 수집
                            detail_links: list[str] = []
                            try:
                                table = page.locator("table.ecl-table, table.cosing-tbl").first
                                if await table.is_visible():
                                    links = await table.locator("a[href*='cosing']").all()
                                    for link in links:
                                        href = await link.get_attribute("href")
                                        if href and _is_detail_link(href):
                                            full_url = href if href.startswith("http") else f"https://ec.europa.eu{href}" if href.startswith("/") else f"{COSING_BASE.rstrip('/')}/{href.lstrip('/')}"
                                            if full_url not in detail_links:
                                                detail_links.append(full_url)
                            except Exception as e:
                                logger.debug("결과 테이블 파싱: %s", e)

                            update_state(
                                "running",
                                processed_count=processed_total,
                                current_search_result_count=len(detail_links),
                            )

                            # 결과 0건이면 건너뜀
                            if not detail_links:
                                last_processed_name = english_name
                                logger.info("검색 결과 없음: %s", english_name)
                                continue

                            # 각 상세 링크 방문
                            for detail_url in detail_links:
                                if check_abort_requested():
                                    update_state(
                                        "aborted",
                                        processed_count=processed_total,
                                        last_ingredient_code=last_processed_name,
                                        ended_at=datetime.now(timezone.utc),
                                        abort_requested=False,
                                    )
                                    return

                                try:
                                    await page.goto(detail_url, wait_until="domcontentloaded", timeout=20000)
                                    if await sleep_with_abort_check(detail_delay):
                                        update_state(
                                            "aborted",
                                            processed_count=processed_total,
                                            last_ingredient_code=last_processed_name,
                                            ended_at=datetime.now(timezone.utc),
                                            abort_requested=False,
                                        )
                                        return

                                    html = await page.content()
                                    parsed = parse_detail_page(
                                        html,
                                        source_url=detail_url,
                                        kcia_english_name=english_name,
                                    )

                                    if parsed.get("inci_name"):
                                        parsed["crawled_at"] = datetime.now(timezone.utc).isoformat()
                                        supabase.table("cosing_ingredients").upsert(
                                            parsed,
                                            on_conflict="inci_name",
                                        ).execute()
                                        csv_writer.writerow(
                                            {k: parsed.get(k, "") for k in CSV_FIELDNAMES}
                                        )
                                        csv_file.flush()
                                        processed_total += 1
                                        update_state(
                                            "running",
                                            processed_count=processed_total,
                                            last_ingredient_code=english_name,
                                        )

                                    await page.go_back()
                                    if await sleep_with_abort_check(request_delay):
                                        update_state(
                                            "aborted",
                                            processed_count=processed_total,
                                            last_ingredient_code=last_processed_name,
                                            ended_at=datetime.now(timezone.utc),
                                            abort_requested=False,
                                        )
                                        return
                                except Exception as e:
                                    logger.warning("상세 페이지 처리 실패 %s: %s", detail_url, e)

                            last_processed_name = english_name
                            if (search_idx + 1) % 10 == 0:
                                logger.info("Progress: %d 검색어 완료, %d건 추출", search_idx + 1, processed_total)

                        except Exception as e:
                            logger.warning("검색 실패 %s: %s", english_name, e)
                            last_processed_name = english_name

                    update_state(
                        "success",
                        processed_count=processed_total,
                        last_ingredient_code=last_processed_name,
                        ended_at=datetime.now(timezone.utc),
                    )
                finally:
                    await browser.close()
        finally:
            csv_file.close()
            logger.info("CSV 저장 완료: %s", csv_path)

    except Exception as e:
        logger.exception("CosIng 크롤 실패: %s", e)
        try:
            update_state("error", error_message=str(e), ended_at=datetime.now(timezone.utc))
        except Exception:
            pass
        raise
