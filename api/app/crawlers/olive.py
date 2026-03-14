"""
올리브영 상품 크롤러 (Playwright)

카테고리 > 스킨케어/메이크업 하위 상품 상세 크롤링
"""

import asyncio
import csv
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.crawlers.olive_parsers import parse_product_detail
from app.config import get_settings

logger = logging.getLogger(__name__)

OLIVE_BASE = "https://www.oliveyoung.co.kr/store"
SOURCE = "olive"

# CSV 컬럼 (olive_skincare 스키마, 상품정보 제공고시까지)
CSV_FIELDNAMES = [
    "goods_no",
    "brand",
    "product_name",
    "price",
    "rating",
    "review_count",
    "category",
    "product_info_disclosure",
    "contents_volume_or_weight",
    "main_specifications",
    "expiration_date",
    "usage_method",
    "manufacturer_info",
    "country_of_origin",
    "ingredients",
    "functionality_approval",
    "precautions",
    "quality_standard",
    "consumer_phone",
    "source_url",
    "crawled_at",
]

# 스킨케어 하위 카테고리 (dispCatNo, 이름)
SKINCARE_CATEGORIES = [
    ("100000100010013", "스킨/토너"),
    ("100000100010014", "에센스/세럼/앰플"),
    ("100000100010015", "크림"),
    ("100000100010016", "로션"),
    ("100000100010010", "미스트/오일"),
    ("100000100010017", "스킨케어세트"),
    ("100000100010018", "스킨케어 디바이스"),
]

# 메이크업 하위 카테고리 (dispCatNo, 이름)
MAKEUP_CATEGORIES = [
    ("100000100020006", "립메이크업"),
    ("100000100020001", "베이스메이크업"),
    ("100000100020007", "아이메이크업"),
]


async def _crawl_single_product_detail(
    page,
    goods_no: str,
    category: str,
    detail_delay: float,
    disp_cat_no: str = "100000100010013",
) -> dict:
    """
    단일 상품 상세 페이지 크롤링.

    상품설명 탭 → 상품정보 제공고시 아코디언까지 추출 (리뷰 탭 미포함)

    Args:
        page: Playwright 페이지
        goods_no: 상품번호
        category: 카테고리명
        detail_delay: 상세 페이지 로딩 대기 시간(초)
        disp_cat_no: 전시 카테고리 번호 (URL용)
    """
    url = f"{OLIVE_BASE}/goods/getGoodsDetail.do?goodsNo={goods_no}&dispCatNo={disp_cat_no}&tab=detail"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(detail_delay)

        data: dict = {
            "goods_no": goods_no,
            "brand": None,
            "product_name": None,
            "price": None,
            "rating": None,
            "review_count": None,
            "category": category,
            "product_info_disclosure": None,
            "contents_volume_or_weight": None,
            "main_specifications": None,
            "expiration_date": None,
            "usage_method": None,
            "manufacturer_info": None,
            "country_of_origin": None,
            "ingredients": None,
            "functionality_approval": None,
            "precautions": None,
            "quality_standard": None,
            "consumer_phone": None,
            "source_url": url,
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }

        # 기본 정보: Playwright locator로 추출
        try:
            brand_el = page.locator(".prd_brand, .brand, [class*='brand']").first
            if await brand_el.count() > 0:
                data["brand"] = (await brand_el.text_content()).strip() or None
        except Exception:
            pass

        try:
            name_el = page.locator("p.prd_name, .prd_name, h3.prd_name").first
            if await name_el.count() > 0:
                data["product_name"] = (await name_el.text_content()).strip() or None
        except Exception:
            pass

        try:
            price_el = page.locator("span.price-2, .prd_price, [class*='price']").first
            if await price_el.count() > 0:
                t = (await price_el.text_content()).replace(",", "").replace("원", "").strip()
                if t and re.search(r"\d+", t):
                    data["price"] = re.search(r"[\d,]+", (await price_el.text_content()) or "").group(0).replace(",", "")
        except Exception:
            pass

        try:
            rating_el = page.locator("[class*='rating'], [class*='star'], [class*='review_score']").first
            if await rating_el.count() > 0:
                t = await rating_el.text_content()
                m = re.search(r"[\d.]+", t or "")
                if m:
                    data["rating"] = m.group(0)
        except Exception:
            pass

        try:
            for sel in [
                "[class*='review_count']",
                "[class*='review_cnt']",
                "[class*='ReviewCount']",
                "[class*='reviewCount']",
                "button:has-text('리뷰')",
                "[aria-label*='리뷰']",
            ]:
                review_el = page.locator(sel).first
                if await review_el.count() > 0:
                    t = await review_el.text_content()
                    m = re.search(r"[\d,]+", (t or "").replace(" ", ""))
                    if m:
                        data["review_count"] = m.group(0).replace(",", "")
                        break
            if not data["review_count"]:
                body_text = await page.locator("body").text_content()
                m = re.search(r"리뷰\s*[\(（]?\s*([\d,]+)\s*[\)）]?", body_text or "")
                if m:
                    data["review_count"] = m.group(1).replace(",", "")
        except Exception:
            pass

        # 1. 상품설명 탭 클릭 (span "상품설명"이 포함된 버튼)
        try:
            desc_tab = page.get_by_role("button", name="상품설명").or_(
                page.locator("button:has-text('상품설명')")
            ).first
            if await desc_tab.count() > 0:
                await desc_tab.click()
                await asyncio.sleep(1)
        except Exception:
            try:
                await page.locator("button:has-text('상품설명')").first.click()
                await asyncio.sleep(1)
            except Exception:
                pass

        # 2. 상품정보 제공고시 아코디언 펼치기
        try:
            acc_btn = page.get_by_role("button", name="상품정보 제공고시").or_(
                page.locator("button.Accordion_accordion-btn__IYjKm, button[class*='accordion-btn']")
            ).first
            if await acc_btn.count() > 0:
                await acc_btn.click()
                await asyncio.sleep(0.8)
        except Exception:
            try:
                await page.locator("button:has-text('상품정보 제공고시')").first.click()
                await asyncio.sleep(0.8)
            except Exception:
                pass

        # 3. 상품정보 제공고시 테이블 th/td 구조화 추출
        try:
            table_parent = page.locator(
                "table.Accordion_table__mcFPq, table[class*='Accordion_table'], "
                ".accordion table, [class*='accordion'] table"
            ).first
            if await table_parent.count() > 0:
                table_html = await table_parent.evaluate("el => el.outerHTML")
                from app.crawlers.olive_parsers import parse_product_info_table
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(table_html, "html.parser")
                parsed_info = parse_product_info_table(soup)
                for k, v in parsed_info.items():
                    if v and k in data:
                        data[k] = v
                if any(parsed_info.values()):
                    data["product_info_disclosure"] = " | ".join(
                        f"{lk}: {v}" for lk, v in parsed_info.items() if v
                    )
        except Exception:
            pass

        # HTML 파서로 폴백 (테이블 미추출 시)
        if not data["product_info_disclosure"] and not data.get("ingredients"):
            html = await page.content()
            parsed = parse_product_detail(html, source_url=url, category=category)
            if parsed.get("product_info_disclosure"):
                data["product_info_disclosure"] = parsed["product_info_disclosure"]
            for k in [
                "contents_volume_or_weight", "main_specifications", "expiration_date",
                "usage_method", "manufacturer_info", "country_of_origin", "ingredients",
                "functionality_approval", "precautions", "quality_standard", "consumer_phone"
            ]:
                if parsed.get(k) and not data.get(k):
                    data[k] = parsed[k]

        # 4. 파서로 브랜드/상품명 등 보완
        if not data["brand"] or not data["product_name"]:
            html = await page.content()
            parsed = parse_product_detail(html, source_url=url, category=category)
            if not data["brand"] and parsed.get("brand"):
                data["brand"] = parsed["brand"]
            if not data["product_name"] and parsed.get("product_name"):
                data["product_name"] = parsed["product_name"]
            if not data["price"] and parsed.get("price"):
                data["price"] = parsed["price"]
            if not data["rating"] and parsed.get("rating"):
                data["rating"] = parsed["rating"]
            if not data["review_count"] and parsed.get("review_count"):
                data["review_count"] = parsed["review_count"]

        return data

    except Exception as e:
        logger.warning("상품 상세 크롤 실패 %s: %s", goods_no, e)
        err_url = f"{OLIVE_BASE}/goods/getGoodsDetail.do?goodsNo={goods_no}&dispCatNo={disp_cat_no}&tab=detail"
        return {
            "goods_no": goods_no,
            "brand": None,
            "product_name": None,
            "price": None,
            "rating": None,
            "review_count": None,
            "category": category,
            "product_info_disclosure": None,
            "contents_volume_or_weight": None,
            "main_specifications": None,
            "expiration_date": None,
            "usage_method": None,
            "manufacturer_info": None,
            "country_of_origin": None,
            "ingredients": None,
            "functionality_approval": None,
            "precautions": None,
            "quality_standard": None,
            "consumer_phone": None,
            "source_url": err_url,
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }


async def crawl_single_product_for_verification(
    goods_no: str = "A000000245459",
) -> dict:
    """
    1단계 검증: 단일 상품 크롤링 테스트.

    Args:
        goods_no: 상품번호 (기본: 바이오더마 하이드라비오 토너)

    Returns:
        추출된 상품 데이터 딕셔너리
    """
    settings = get_settings()
    delay = getattr(settings, "olive_detail_delay_sec", 2.0)
    headless = getattr(settings, "olive_headless", True)

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="ko-KR",
        )
        page = await context.new_page()

        try:
            result = await _crawl_single_product_detail(
                page, goods_no, "스킨/토너", delay,
                disp_cat_no="100000100010013",
            )
            return result
        finally:
            await browser.close()


async def run_olive_skincare_crawl(
    categories: Optional[list[tuple[str, str]]] = None,
    max_products_per_category: Optional[int] = None,
) -> Path:
    """
    스킨케어 전체 상품 크롤링 (2~3단계).

    Args:
        categories: (dispCatNo, 이름) 리스트. None이면 SKINCARE_CATEGORIES 사용.
        max_products_per_category: 카테고리당 최대 상품 수. None이면 제한 없음.

    Returns:
        저장된 CSV 파일 경로
    """
    settings = get_settings()
    delay = getattr(settings, "olive_detail_delay_sec", 2.0)
    request_delay = getattr(settings, "olive_request_delay_sec", 1.0)
    headless = getattr(settings, "olive_headless", True)
    download_dir = Path(getattr(settings, "olive_download_dir", "olive_downloads"))

    cats = categories or SKINCARE_CATEGORIES
    api_root = Path(__file__).resolve().parent.parent.parent
    workspace_root = api_root.parent
    out_dir = workspace_root / download_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path = out_dir / f"olive_skincare_{timestamp}.csv"

    from playwright.async_api import async_playwright

    all_goods: list[tuple[str, str]] = []  # (goods_no, category)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="ko-KR",
        )
        page = await context.new_page()

        try:
            for disp_cat_no, cat_name in cats:
                cat_goods: list[tuple[str, str]] = []
                page_idx = 1
                seen_in_cat = set()

                while True:
                    url = f"{OLIVE_BASE}/display/getMCategoryList.do?dispCatNo={disp_cat_no}&fltDispCat=&pageIdx={page_idx}"
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=8000)
                        except Exception:
                            pass
                        await asyncio.sleep(2)

                        # 상품 링크: a[href*='getGoodsDetail.do'] 또는 data-ref-goodsno (olive.html 구조)
                        links = await page.locator("a[href*='getGoodsDetail.do']").all()
                        if not links:
                            links = await page.locator("[data-ref-goodsno]").all()
                        page_count = 0
                        for link in links:
                            if max_products_per_category and len(cat_goods) >= max_products_per_category:
                                break
                            gno = None
                            href = await link.get_attribute("href")
                            if href:
                                m = re.search(r"goodsNo=([A-Za-z0-9]+)", href)
                                if m:
                                    gno = m.group(1)
                            if not gno:
                                gno = await link.get_attribute("data-ref-goodsno")
                            if gno and gno not in seen_in_cat:
                                seen_in_cat.add(gno)
                                cat_goods.append((gno, cat_name))
                                page_count += 1

                        all_goods.extend(cat_goods[-page_count:] if page_count else [])

                        if page_count == 0:
                            break

                        if max_products_per_category and len(cat_goods) >= max_products_per_category:
                            break

                        # 다음 페이지 존재 여부 확인
                        next_btn = page.locator("a:has-text('다음'), .next, [class*='page-next']").first
                        if await next_btn.count() == 0 or not await next_btn.is_visible():
                            break
                        page_idx += 1
                        await asyncio.sleep(request_delay)

                    except Exception as e:
                        logger.warning("카테고리 %s page %d 수집 실패: %s", cat_name, page_idx, e)
                        break

                logger.info("카테고리 %s: %d개 상품 수집", cat_name, len(cat_goods))
                await asyncio.sleep(request_delay)

            # 중복 제거 (마지막 카테고리 기준)
            seen_no = set()
            unique_goods: list[tuple[str, str]] = []
            for gno, cat in reversed(all_goods):
                if gno not in seen_no:
                    seen_no.add(gno)
                    unique_goods.append((gno, cat))
            unique_goods.reverse()

            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
                writer.writeheader()

                for i, (gno, cat) in enumerate(unique_goods):
                    disp_no = next((d for d, c in cats if c == cat), "100000100010013")
                    try:
                        row = await _crawl_single_product_detail(
                            page, gno, cat, delay, disp_cat_no=disp_no
                        )
                        writer.writerow({k: row.get(k, "") for k in CSV_FIELDNAMES})
                        f.flush()
                        if (i + 1) % 5 == 0:
                            logger.info("Progress: %d/%d", i + 1, len(unique_goods))
                    except Exception as e:
                        logger.warning("상품 %s 크롤 실패: %s", gno, e)

                    await asyncio.sleep(request_delay)

        finally:
            await browser.close()

    logger.info("CSV 저장: %s", csv_path)
    return csv_path


async def run_olive_makeup_crawl(
    categories: Optional[list[tuple[str, str]]] = None,
    max_products_per_category: Optional[int] = None,
) -> Path:
    """
    메이크업 전체 상품 크롤링.

    Args:
        categories: (dispCatNo, 이름) 리스트. None이면 MAKEUP_CATEGORIES 사용.
        max_products_per_category: 카테고리당 최대 상품 수. None이면 제한 없음.

    Returns:
        저장된 CSV 파일 경로
    """
    settings = get_settings()
    delay = getattr(settings, "olive_detail_delay_sec", 2.0)
    request_delay = getattr(settings, "olive_request_delay_sec", 1.0)
    headless = getattr(settings, "olive_headless", True)
    download_dir = Path(getattr(settings, "olive_download_dir", "olive_downloads"))

    cats = categories or MAKEUP_CATEGORIES
    api_root = Path(__file__).resolve().parent.parent.parent
    workspace_root = api_root.parent
    out_dir = workspace_root / download_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path = out_dir / f"olive_makeup_{timestamp}.csv"

    from playwright.async_api import async_playwright

    all_goods: list[tuple[str, str]] = []  # (goods_no, category)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="ko-KR",
        )
        page = await context.new_page()

        try:
            for disp_cat_no, cat_name in cats:
                cat_goods: list[tuple[str, str]] = []
                page_idx = 1
                seen_in_cat = set()

                while True:
                    url = f"{OLIVE_BASE}/display/getMCategoryList.do?dispCatNo={disp_cat_no}&fltDispCat=&pageIdx={page_idx}"
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=8000)
                        except Exception:
                            pass
                        await asyncio.sleep(2)

                        links = await page.locator("a[href*='getGoodsDetail.do']").all()
                        if not links:
                            links = await page.locator("[data-ref-goodsno]").all()
                        page_count = 0
                        for link in links:
                            if max_products_per_category and len(cat_goods) >= max_products_per_category:
                                break
                            gno = None
                            href = await link.get_attribute("href")
                            if href:
                                m = re.search(r"goodsNo=([A-Za-z0-9]+)", href)
                                if m:
                                    gno = m.group(1)
                            if not gno:
                                gno = await link.get_attribute("data-ref-goodsno")
                            if gno and gno not in seen_in_cat:
                                seen_in_cat.add(gno)
                                cat_goods.append((gno, cat_name))
                                page_count += 1

                        all_goods.extend(cat_goods[-page_count:] if page_count else [])

                        if page_count == 0:
                            break

                        if max_products_per_category and len(cat_goods) >= max_products_per_category:
                            break

                        next_btn = page.locator("a:has-text('다음'), .next, [class*='page-next']").first
                        if await next_btn.count() == 0 or not await next_btn.is_visible():
                            break
                        page_idx += 1
                        await asyncio.sleep(request_delay)

                    except Exception as e:
                        logger.warning("카테고리 %s page %d 수집 실패: %s", cat_name, page_idx, e)
                        break

                logger.info("카테고리 %s: %d개 상품 수집", cat_name, len(cat_goods))
                await asyncio.sleep(request_delay)

            seen_no = set()
            unique_goods: list[tuple[str, str]] = []
            for gno, cat in reversed(all_goods):
                if gno not in seen_no:
                    seen_no.add(gno)
                    unique_goods.append((gno, cat))
            unique_goods.reverse()

            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
                writer.writeheader()

                for i, (gno, cat) in enumerate(unique_goods):
                    disp_no = next((d for d, c in cats if c == cat), "100000100020006")
                    try:
                        row = await _crawl_single_product_detail(
                            page, gno, cat, delay, disp_cat_no=disp_no
                        )
                        writer.writerow({k: row.get(k, "") for k in CSV_FIELDNAMES})
                        f.flush()
                        if (i + 1) % 5 == 0:
                            logger.info("Progress: %d/%d", i + 1, len(unique_goods))
                    except Exception as e:
                        logger.warning("상품 %s 크롤 실패: %s", gno, e)

                    await asyncio.sleep(request_delay)

        finally:
            await browser.close()

    logger.info("CSV 저장: %s", csv_path)
    return csv_path
