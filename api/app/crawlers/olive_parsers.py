"""
올리브영 상품 상세 페이지 HTML 파서
"""

import re
from typing import Optional

from bs4 import BeautifulSoup

# 상품정보 제공고시 테이블: 한글 라벨 -> CSV 컬럼명 매핑
PRODUCT_INFO_LABEL_MAP = {
    "내용물의 용량 또는 중량": "contents_volume_or_weight",
    "제품 주요 사양": "main_specifications",
    "사용기한(또는 개봉 후 사용기간)": "expiration_date",
    "사용방법": "usage_method",
    "화장품제조업자,화장품책임판매업자 및 맞춤형화장품판매업자": "manufacturer_info",
    "제조국": "country_of_origin",
    "화장품법에 따라 기재해야 하는 모든 성분": "ingredients",
    "기능성 화장품 식품의약품안전처 심사필 여부": "functionality_approval",
    "사용할 때의 주의사항": "precautions",
    "품질보증기준": "quality_standard",
    "소비자상담 전화번호": "consumer_phone",
}


def _text(el, default: str = "") -> str:
    """요소에서 텍스트 추출 (공백 정리)."""
    if el is None:
        return default
    text = el.get_text(separator=" ", strip=True)
    return " ".join(text.split()) if text else default


def parse_product_info_table(table) -> dict[str, Optional[str]]:
    """
    상품정보 제공고시 테이블에서 th/td 쌍을 추출.

    Args:
        table: BeautifulSoup 테이블 요소

    Returns:
        {column_name: value} 딕셔너리 (PRODUCT_INFO_LABEL_MAP 기준)
    """
    result: dict[str, Optional[str]] = {v: None for v in PRODUCT_INFO_LABEL_MAP.values()}
    if not table:
        return result

    rows = table.select("tbody tr, tr")
    for row in rows:
        th = row.select_one("th")
        td = row.select_one("td")
        if not th or not td:
            continue
        label = _text(th).strip()
        value = _text(td).strip()
        if not label or not value:
            continue
        # 정확 매칭 후 부분 매칭 (라벨이 잘려 있을 수 있음)
        col_name = PRODUCT_INFO_LABEL_MAP.get(label)
        if not col_name:
            for k, v in PRODUCT_INFO_LABEL_MAP.items():
                if k in label or label in k:
                    col_name = v
                    break
        if col_name:
            result[col_name] = value

    return result


def _extract_goods_no_from_url(url: str) -> Optional[str]:
    """URL에서 goodsNo 파라미터 추출."""
    if not url:
        return None
    m = re.search(r"goodsNo=([A-Za-z0-9]+)", url)
    return m.group(1) if m else None


def parse_product_detail(
    html: str,
    source_url: str = "",
    category: Optional[str] = None,
) -> dict:
    """
    올리브영 상품 상세 페이지 HTML에서 정보 추출.

    Args:
        html: 상세 페이지 HTML
        source_url: 페이지 URL (저장용)
        category: 카테고리명 (스킨/토너 등)

    Returns:
        olive_skincare 스키마용 딕셔너리
    """
    soup = BeautifulSoup(html, "html.parser")
    goods_no = _extract_goods_no_from_url(source_url)

    data: dict[str, Optional[str]] = {
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
        "source_url": source_url or None,
        "crawled_at": None,
    }

    # 브랜드: prd_brand, .brand, brand_name 등
    for sel in [".prd_brand", ".brand", ".brand_name", "[class*='brand']"]:
        el = soup.select_one(sel)
        if el and _text(el):
            data["brand"] = _text(el)
            break

    # 상품명: prd_name, .prd_name, h3.prd_name 등
    for sel in ["p.prd_name", ".prd_name", "h3.prd_name", "[class*='prd_name']", "h3"]:
        el = soup.select_one(sel)
        if el and _text(el) and len(_text(el)) > 2:
            data["product_name"] = _text(el)
            break

    # 가격: price-2, prd_price, .price 등
    for sel in ["span.price-2", ".price-2", ".prd_price", "[class*='price']"]:
        for el in soup.select(sel):
            t = _text(el).replace(",", "").replace("원", "").strip()
            if t and t.isdigit():
                data["price"] = t
                break
        if data["price"]:
            break

    # 별점
    for sel in [
        ".rating",
        ".star",
        "[class*='rating']",
        "[class*='star']",
        "[class*='review_score']",
    ]:
        el = soup.select_one(sel)
        if el:
            t = _text(el)
            m = re.search(r"[\d.]+", t)
            if m:
                data["rating"] = m.group(0)
                break

    # 리뷰 수
    for sel in [
        ".review_count",
        ".review_cnt",
        "[class*='review_count']",
        "[class*='review_cnt']",
        "[class*='ReviewCount']",
        "[class*='reviewCount']",
        "[aria-label*='리뷰']",
    ]:
        el = soup.select_one(sel)
        if el:
            t = _text(el).replace(",", "").replace(" ", "")
            m = re.search(r"\d+", t)
            if m:
                data["review_count"] = m.group(0)
                break
    if not data["review_count"]:
        body = soup.select_one("body")
        if body:
            body_text = body.get_text(separator=" ", strip=True)
            m = re.search(r"리뷰\s*[\(（]?\s*([\d,]+)\s*[\)）]?", body_text)
            if m:
                data["review_count"] = m.group(1).replace(",", "")

    # 상품정보 제공고시: 테이블 th/td 기반 구조화 추출
    table = soup.select_one(
        "table.Accordion_table__mcFPq, table[class*='Accordion_table'], "
        ".accordion table, [class*='accordion'] table"
    )
    if table:
        parsed_info = parse_product_info_table(table)
        for col_name, val in parsed_info.items():
            if val and col_name in data:
                data[col_name] = val
        # 레거시: 전체 텍스트도 product_info_disclosure에 저장
        if any(parsed_info.values()):
            data["product_info_disclosure"] = " | ".join(
                f"{k}: {v}" for k, v in parsed_info.items() if v
            )

    # 폴백: 아코디언 전체 텍스트
    if not data.get("product_info_disclosure"):
        acc = soup.select_one(".product_info_disclosure, [class*='제공고시'], [class*='accordion']")
        if acc:
            data["product_info_disclosure"] = _text(acc)
        for sel in ["#product_info_table", ".product_info_table", "[id*='product_info']"]:
            acc = soup.select_one(sel)
            if acc:
                data["product_info_disclosure"] = _text(acc)
                break

    return {k: v if v else None for k, v in data.items()}
