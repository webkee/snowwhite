#!/usr/bin/env python3
"""1단계 검증: 단일 상품(goodsNo=A000000245459) 크롤링 테스트."""

import asyncio
import csv
import sys
from pathlib import Path

# api 루트를 path에 추가
api_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_root))

from app.crawlers.olive import (
    CSV_FIELDNAMES,
    crawl_single_product_for_verification,
)


async def main() -> None:
    print("올리브영 단일 상품 크롤링 검증 (goodsNo=A000000245459)")
    print("상품설명 탭 → 상품정보 제공고시까지")
    print("-" * 50)
    result = await crawl_single_product_for_verification("A000000245459")
    print("\n추출 결과:")
    for k, v in result.items():
        val = (v[:100] + "...") if v and len(str(v)) > 100 else v
        print(f"  {k}: {val}")

    # CSV 1행 저장
    out_dir = Path(__file__).resolve().parent.parent.parent / "olive_downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "olive_verify_single.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerow({k: result.get(k, "") for k in CSV_FIELDNAMES})
    print(f"\nCSV 저장: {csv_path}")


if __name__ == "__main__":
    asyncio.run(main())
