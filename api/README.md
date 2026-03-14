# KCA 성분 크롤러 API

대한화장품협회 성분사전 크롤링 API (FastAPI).

## 설정

```bash
cp .env.example .env
# .env 에 SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY 설정
```

## Supabase 마이그레이션

다음 SQL 파일을 순서대로 Supabase SQL Editor에서 실행하세요.

1. `supabase/migrations/20240312000000_create_kcia_tables.sql`
2. `supabase/migrations/20240312000001_add_abort_requested_to_crawl_state.sql`
3. `supabase/migrations/20240313000000_create_cosing_tables.sql`
4. `supabase/migrations/20260314000000_create_olive_products.sql`

## 올리브영 CSV 마이그레이션

```bash
cd api
python -m scripts.migrate_olive_csv_to_supabase --all    # 스킨케어 + 메이크업
python -m scripts.migrate_olive_csv_to_supabase --skincare
python -m scripts.migrate_olive_csv_to_supabase --makeup
```

## 실행

```bash
pip3 install -r requirements.txt   # 또는 python3 -m pip install -r requirements.txt
playwright install chromium         # CosIng 크롤러용 (최초 1회)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API

- `GET /health` - 헬스 체크

### KCA 성분사전
- `POST /crawl/kcia/start?resume=false` - 크롤 시작 (resume=true 이어받기)
- `POST /crawl/kcia/abort` - 실행 중인 크롤 중단 요청
- `POST /crawl/kcia/reset` - 크롤 상태 초기화
- `GET /crawl/kcia/status` - 진행 상태
- `GET /crawl/kcia/export/json` - JSON 다운로드
- `GET /crawl/kcia/export/csv` - CSV 다운로드

### CosIng (EU 화장품 성분 DB)
- `POST /crawl/cosing/start?resume=false` - 크롤 시작 (kcia_ingredients.english_name 기반 검색)
- `POST /crawl/cosing/abort` - 실행 중인 크롤 중단 요청
- `POST /crawl/cosing/reset` - 크롤 상태 초기화
- `GET /crawl/cosing/status` - 진행 상태
- `GET /crawl/cosing/export/json` - JSON 다운로드
- `GET /crawl/cosing/export/csv` - CSV 다운로드

## 문제 해결

- **"크롤이 이미 실행 중입니다"**: 이전 크롤이 에러로 중단되어 status가 `running`으로 남은 경우. `POST /crawl/kcia/reset` 또는 `POST /crawl/cosing/reset` 호출 후 다시 시작하세요.
- **CosIng 크롤 실패**: `playwright install chromium` 실행 여부 확인. `.env`에서 `COSING_SEARCH_DELAY_SEC` 등 지연 시간을 늘려보세요.
