#!/usr/bin/env python3
"""
올리브영 스킨케어/메이크업 CSV 파일을 Supabase olive_products 테이블로 마이그레이션합니다.

사용법:
    cd api
    python -m scripts.migrate_olive_csv_to_supabase --all
    python -m scripts.migrate_olive_csv_to_supabase --skincare
    python -m scripts.migrate_olive_csv_to_supabase --makeup
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

# api/ 기준으로 실행되므로 app 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

api_dir = Path(__file__).resolve().parent.parent
env_path = api_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)

# 프로젝트 루트 (api의 상위)
PROJECT_ROOT = api_dir.parent
OLIVE_DOWNLOAD_DIR = Path(os.getenv("OLIVE_DOWNLOAD_DIR", "olive_downloads"))
OLIVE_CSV_BASE = PROJECT_ROOT / OLIVE_DOWNLOAD_DIR

# 추출된 CSV 파일 (가장 최신/풀 버전 우선)
SKINCARE_CSV = OLIVE_CSV_BASE / "olive_skincare_20260313_100433.csv"
MAKEUP_CSV = OLIVE_CSV_BASE / "olive_makeup_20260313_133547.csv"

BATCH_SIZE = 100


def _parse_int(value: str | None) -> int | None:
    """문자열을 정수로 변환. 빈 문자열·None이면 None."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _parse_float(value: str | None) -> float | None:
    """문자열을 실수로 변환. 빈 문자열·None이면 None."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_datetime(value: str | None) -> str | None:
    """ISO 8601 문자열을 그대로 반환 (Supabase timestamptz 호환). 빈 문자열이면 None."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    return value.strip()


def _str_or_none(value: Any) -> str | None:
    """값을 문자열로. 빈 문자열이면 None."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def load_csv_rows(filepath: Path, encoding: str = "utf-8-sig") -> Iterator[dict[str, Any]]:
    """CSV 파일을 행 단위로 읽어 dict yield. utf-8-sig로 BOM 제거."""
    with open(filepath, "r", encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def row_to_record(row: dict[str, Any], product_type: str) -> dict[str, Any]:
    """CSV 행을 Supabase olive_products 레코드로 변환."""
    return {
        "product_type": product_type,
        "goods_no": _str_or_none(row.get("goods_no")) or "",
        "brand": _str_or_none(row.get("brand")),
        "product_name": _str_or_none(row.get("product_name")),
        "price": _parse_int(row.get("price")),
        "rating": _parse_float(row.get("rating")),
        "review_count": _parse_int(row.get("review_count")),
        "category": _str_or_none(row.get("category")),
        "product_info_disclosure": _str_or_none(row.get("product_info_disclosure")),
        "contents_volume_or_weight": _str_or_none(row.get("contents_volume_or_weight")),
        "main_specifications": _str_or_none(row.get("main_specifications")),
        "expiration_date": _str_or_none(row.get("expiration_date")),
        "usage_method": _str_or_none(row.get("usage_method")),
        "manufacturer_info": _str_or_none(row.get("manufacturer_info")),
        "country_of_origin": _str_or_none(row.get("country_of_origin")),
        "ingredients": _str_or_none(row.get("ingredients")),
        "functionality_approval": _str_or_none(row.get("functionality_approval")),
        "precautions": _str_or_none(row.get("precautions")),
        "quality_standard": _str_or_none(row.get("quality_standard")),
        "consumer_phone": _str_or_none(row.get("consumer_phone")),
        "source_url": _str_or_none(row.get("source_url")),
        "crawled_at": _parse_datetime(row.get("crawled_at")),
    }


def migrate_file(
    client: Any,
    filepath: Path,
    product_type: str,
) -> tuple[int, int]:
    """단일 CSV 파일을 Supabase에 upsert. (성공 건수, 실패 건수) 반환."""
    success = 0
    failed = 0
    batch: list[dict[str, Any]] = []

    for row in load_csv_rows(filepath):
        record = row_to_record(row, product_type)
        if not record.get("goods_no"):
            failed += 1
            continue
        batch.append(record)

        if len(batch) >= BATCH_SIZE:
            try:
                client.table("olive_products").upsert(
                    batch,
                    on_conflict="goods_no,product_type",
                ).execute()
                success += len(batch)
            except Exception as e:
                print(f"  [ERROR] 배치 upsert 실패: {e}", file=sys.stderr)
                failed += len(batch)
            batch = []

    if batch:
        try:
            client.table("olive_products").upsert(
                batch,
                on_conflict="goods_no,product_type",
            ).execute()
            success += len(batch)
        except Exception as e:
            print(f"  [ERROR] 마지막 배치 upsert 실패: {e}", file=sys.stderr)
            failed += len(batch)

    return success, failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="올리브영 CSV를 Supabase olive_products로 마이그레이션"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="스킨케어 + 메이크업 모두")
    group.add_argument("--skincare", action="store_true", help="스킨케어만")
    group.add_argument("--makeup", action="store_true", help="메이크업만")
    args = parser.parse_args()

    # Supabase 클라이언트
    try:
        from app.db.supabase_client import get_supabase

        client = get_supabase()
    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}", file=sys.stderr)
        sys.exit(1)

    # olive_products 테이블 존재 여부 확인
    try:
        client.table("olive_products").select("id").limit(1).execute()
    except Exception as e:
        err_str = str(e)
        if "olive_products" in err_str or "PGRST205" in err_str:
            print(
                "❌ olive_products 테이블이 없습니다.\n"
                "   Supabase SQL Editor에서 아래 마이그레이션을 먼저 실행하세요:\n"
                "   supabase/migrations/20260314000000_create_olive_products.sql",
                file=sys.stderr,
            )
        else:
            print(f"❌ 테이블 확인 실패: {e}", file=sys.stderr)
        sys.exit(1)

    total_success = 0
    total_failed = 0
    start = datetime.now()

    if args.all or args.skincare:
        if not SKINCARE_CSV.exists():
            print(f"⚠ 스킨케어 CSV 없음: {SKINCARE_CSV}", file=sys.stderr)
        else:
            print(f"[스킨케어] {SKINCARE_CSV}")
            s, f = migrate_file(client, SKINCARE_CSV, "skincare")
            total_success += s
            total_failed += f
            print(f"  → 성공 {s}건, 실패 {f}건")

    if args.all or args.makeup:
        if not MAKEUP_CSV.exists():
            print(f"⚠ 메이크업 CSV 없음: {MAKEUP_CSV}", file=sys.stderr)
        else:
            print(f"[메이크업] {MAKEUP_CSV}")
            s, f = migrate_file(client, MAKEUP_CSV, "makeup")
            total_success += s
            total_failed += f
            print(f"  → 성공 {s}건, 실패 {f}건")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n=== 완료: 성공 {total_success}건, 실패 {total_failed}건 ({elapsed:.1f}초) ===")
    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
