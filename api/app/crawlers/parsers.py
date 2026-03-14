"""
KCA 성분사전 HTML 파서
"""

import re
from typing import Optional
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

# 리스트 페이지 URL
LIST_BASE = "https://kcia.or.kr/cid/search/ingd_list.php"
DETAIL_BASE = "https://kcia.or.kr/cid/search/ingd_view.php"


def parse_list_page(html: str, base_url: str = LIST_BASE) -> tuple[list[str], Optional[int]]:
    """
    리스트 페이지에서 성분 코드(no) 목록과 총 건수 추출.

    Args:
        html: 리스트 페이지 HTML
        base_url: 기준 URL (미사용, 호환용)

    Returns:
        (성분코드 목록, 총 건수). 총 건수 추출 실패 시 None.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 성분코드(no) 추출: a[href*="ingd_view.php?no="]
    ids: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "ingd_view.php" in href and "no=" in href:
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            for no in params.get("no", []):
                if no and no not in seen:
                    seen.add(no)
                    ids.append(no)

    # 총 건수: "총 N건의 자료"
    total: Optional[int] = None
    text = soup.get_text()
    match = re.search(r"총\s*([\d,]+)\s*건의\s*자료", text)
    if match:
        group_val = match.group(1)
        # tuple 등 비문자열이 반환될 경우 대비 (표준 re.group(1)은 str 반환)
        if isinstance(group_val, tuple):
            group_val = group_val[0] if group_val else ""
        # re.sub 사용: .replace() 호출 시 tuple에서 AttributeError 방지
        num_str = re.sub(r",", "", str(group_val))
        total = int(num_str) if num_str.strip() else None

    return ids, total


def parse_detail_page(html: str, ingredient_code: str) -> dict:
    """
    상세 페이지에서 성분 정보 추출.

    Args:
        html: 상세 페이지 HTML
        ingredient_code: 성분코드 (no)

    Returns:
        성분 정보 dict. 키: ingredient_code, ingredient_name, old_name,
        english_name, cas_number, origin_definition, blend_purpose, source_url
    """
    soup = BeautifulSoup(html, "html.parser")
    source_url = f"{DETAIL_BASE}?no={ingredient_code}"

    result: dict = {
        "ingredient_code": ingredient_code,
        "ingredient_name": None,
        "old_name": None,
        "english_name": None,
        "cas_number": None,
        "origin_definition": None,
        "blend_purpose": None,
        "source_url": source_url,
    }

    # div.form_area 내 table.table_li.t
    form_area = soup.find("div", class_="form_area")
    if not form_area:
        return result

    table = form_area.find("table", class_=re.compile(r"table_li"))
    if not table:
        return result

    tbody = table.find("tbody") or table
    rows = tbody.find_all("tr")

    label_to_key = {
        "성분코드": "ingredient_code",
        "성분명": "ingredient_name",
        "구명칭": "old_name",
        "영문명": "english_name",
        "기원 및 정의": "origin_definition",
        "배합목적": "blend_purpose",
    }

    for row in rows:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        i = 0
        while i < len(cells):
            cell = cells[i]
            label = (cell.get_text() or "").strip()
            key = label_to_key.get(label)
            if key and i + 1 < len(cells):
                next_cell = cells[i + 1]
                value = (next_cell.get_text() or "").strip()
                if not value and key == "blend_purpose":
                    link = next_cell.find("a") or row.find("a", href=re.compile(r"INGD_PURPOSE"))
                    if link:
                        value = (link.get_text() or "").strip()
                if value:
                    result[key] = value
                i += 2  # label + value 소비
            else:
                i += 1

    return result
