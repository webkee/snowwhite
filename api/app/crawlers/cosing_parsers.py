"""
CosIng 상세 페이지 HTML 파서
"""

import re
from typing import Optional

from bs4 import BeautifulSoup


def _extract_cosing_id_from_url(url: str) -> Optional[str]:
    """
    CosIng 상세 URL에서 cosing_id 추출.
    예: https://ec.europa.eu/.../details/101976 -> '101976'
    """
    if not url:
        return None
    m = re.search(r"/details/(\d+)(?:/|$|\?)", url)
    return m.group(1) if m else None


def _cell_text(cell) -> str:
    """테이블 셀에서 텍스트 추출 (태그 제거, 공백 정리)."""
    if cell is None:
        return ""
    text = cell.get_text(separator=" ", strip=True)
    return " ".join(text.split()) if text else ""


def _extract_list_items(cell) -> str:
    """ul/li 또는 a 태그 목록에서 텍스트를 추출하여 쉼표로 연결."""
    if cell is None:
        return ""
    items: list[str] = []
    for a in cell.find_all("a"):
        t = _cell_text(a)
        if t:
            items.append(t)
    if items:
        return ", ".join(items)
    for li in cell.find_all("li", class_="ecl-unordered-list__item"):
        t = _cell_text(li)
        if t:
            items.append(t)
    return ", ".join(items) if items else _cell_text(cell)


def parse_detail_page(html: str, source_url: str = "", kcia_english_name: Optional[str] = None) -> dict:
    """
    CosIng 상세 페이지 테이블에서 성분 정보 추출.

    Args:
        html: 상세 페이지 HTML
        source_url: 페이지 URL (저장용)
        kcia_english_name: 검색에 사용한 kcia_ingredients.english_name

    Returns:
        cosing_ingredients 테이블용 딕셔너리
    """
    soup = BeautifulSoup(html, "html.parser")
    cosing_id = _extract_cosing_id_from_url(source_url)
    data: dict[str, Optional[str]] = {
        "cosing_id": cosing_id,
        "inci_name": None,
        "description": None,
        "cas_number": None,
        "ec_number": None,
        "identified_ingredients": None,
        "cosmetics_regulation_provisions": None,
        "functions": None,
        "sccs_opinions": None,
        "kcia_english_name": kcia_english_name,
        "source_url": source_url or None,
    }

    rows = soup.find_all("tr", class_="ecl-table__row")
    for row in rows:
        cells = row.find_all("td", class_="ecl-table__cell")
        if len(cells) < 2:
            continue
        label = _cell_text(cells[0]).strip()
        value_cell = cells[1]

        if "INCI Name" in label:
            data["inci_name"] = _cell_text(value_cell) or None
        elif "Description" in label:
            data["description"] = _cell_text(value_cell) or None
        elif "CAS #" in label:
            data["cas_number"] = _cell_text(value_cell) or None
        elif "EC #" in label:
            data["ec_number"] = _cell_text(value_cell) or None
        elif "Identified INGREDIENTS" in label or "Identified ingredients" in label:
            data["identified_ingredients"] = _extract_list_items(value_cell) or _cell_text(value_cell) or None
        elif "Cosmetics Regulation provisions" in label:
            data["cosmetics_regulation_provisions"] = _extract_list_items(value_cell) or _cell_text(value_cell) or None
        elif "Functions" in label:
            data["functions"] = _extract_list_items(value_cell) or None
        elif "SCCS opinions" in label:
            data["sccs_opinions"] = _extract_list_items(value_cell) or _cell_text(value_cell) or None

    return {k: v if v else None for k, v in data.items()}
