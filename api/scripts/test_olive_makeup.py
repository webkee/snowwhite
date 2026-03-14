#!/usr/bin/env python3
"""메이크업 카테고리별 상품 목록 수집 테스트."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")

api_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_root))

from app.crawlers.olive import (
    MAKEUP_CATEGORIES,
    run_olive_makeup_crawl,
)


async def main() -> None:
    parser = argparse.ArgumentParser(description="올리브영 메이크업 크롤링")
    parser.add_argument(
        "--full",
        action="store_true",
        help="제한 없이 메이크업 전체 상품 크롤링",
    )
    parser.add_argument(
        "-n",
        "--max-per-category",
        type=int,
        default=3,
        metavar="N",
        help="카테고리당 최대 상품 수 (기본 3, --full 시 무시)",
    )
    args = parser.parse_args()

    if args.full:
        print("올리브영 메이크업 전체 상품 크롤링")
        max_per_cat = None
        categories = MAKEUP_CATEGORIES
    else:
        print("올리브영 카테고리 상품 목록 수집 테스트 (립메이크업, 제한 적용)")
        max_per_cat = args.max_per_category
        categories = [MAKEUP_CATEGORIES[0]]

    print("-" * 50)
    csv_path = await run_olive_makeup_crawl(
        categories=categories,
        max_products_per_category=max_per_cat,
    )
    print(f"\n완료: {csv_path}")
    if csv_path.exists():
        lines = csv_path.read_text(encoding="utf-8-sig").strip().split("\n")
        print(f"CSV 행 수: {len(lines) - 1}개 상품")


if __name__ == "__main__":
    asyncio.run(main())
