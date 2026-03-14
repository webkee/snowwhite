#!/usr/bin/env python3
"""
Supabase 연결 테스트 스크립트
"""

import os
import sys

# api/ 기준으로 실행되므로 app 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env 로드 (api 디렉토리 기준)
from pathlib import Path
from dotenv import load_dotenv

api_dir = Path(__file__).resolve().parent.parent
env_path = api_dir / ".env"
if not env_path.exists():
    env_path = api_dir / ".env.example"
load_dotenv(env_path)


def main() -> None:
    print("=== Supabase 연결 테스트 ===\n")

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    if not url:
        print("❌ SUPABASE_URL이 설정되지 않았습니다.")
        print("   api/.env 파일에 SUPABASE_URL을 설정하세요.")
        sys.exit(1)
    if not key:
        print("❌ SUPABASE_SERVICE_ROLE_KEY가 설정되지 않았습니다.")
        print("   api/.env 파일에 SUPABASE_SERVICE_ROLE_KEY를 설정하세요.")
        sys.exit(1)

    print(f"✓ SUPABASE_URL: {url[:50]}...")
    print(f"✓ SUPABASE_SERVICE_ROLE_KEY: {key[:20]}...\n")

    try:
        from supabase import create_client

        client = create_client(url, key)
        print("✓ Supabase 클라이언트 생성 성공\n")

        # crawl_state 테이블 조회 시도
        try:
            result = client.table("crawl_state").select("source, status").limit(1).execute()
            print(f"✓ crawl_state 테이블 조회 성공: {len(result.data)}건")
        except Exception as e:
            print(f"⚠ crawl_state 테이블 조회 실패 (테이블 미생성 가능): {e}")
            print("  → Supabase SQL Editor에서 마이그레이션을 실행하세요.\n")

        # kcia_ingredients 테이블 조회 시도
        try:
            result = client.table("kcia_ingredients").select("ingredient_code").limit(1).execute()
            print(f"✓ kcia_ingredients 테이블 조회 성공: {len(result.data)}건")
        except Exception as e:
            print(f"⚠ kcia_ingredients 테이블 조회 실패 (테이블 미생성 가능): {e}")

        print("\n=== Supabase 연결 테스트 완료 ===")

    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
