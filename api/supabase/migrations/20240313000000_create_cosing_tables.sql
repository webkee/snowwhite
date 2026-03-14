-- CosIng 크롤러 테이블

CREATE TABLE IF NOT EXISTS cosing_ingredients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  inci_name text NOT NULL,
  description text,
  cas_number varchar(50),
  ec_number varchar(50),
  identified_ingredients text,
  cosmetics_regulation_provisions text,
  functions text,
  sccs_opinions text,
  kcia_english_name text,
  source_url text,
  crawled_at timestamptz DEFAULT now(),
  UNIQUE(inci_name)
);

CREATE INDEX IF NOT EXISTS idx_cosing_ingredients_inci_name ON cosing_ingredients(inci_name);
CREATE INDEX IF NOT EXISTS idx_cosing_ingredients_kcia_english_name ON cosing_ingredients(kcia_english_name);

-- crawl_state에 CosIng 진행 상태용 컬럼 추가
ALTER TABLE crawl_state ADD COLUMN IF NOT EXISTS current_search_keyword text;
ALTER TABLE crawl_state ADD COLUMN IF NOT EXISTS current_search_result_count int;

-- last_ingredient_code 확장: CosIng는 english_name 저장 (varchar(20) 초과 가능)
ALTER TABLE crawl_state ALTER COLUMN last_ingredient_code TYPE text;
