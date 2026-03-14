-- KCA 성분 크롤러 테이블

CREATE TABLE IF NOT EXISTS kcia_ingredients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ingredient_code varchar(20) UNIQUE NOT NULL,
  ingredient_name text,
  old_name text,
  english_name text,
  cas_number varchar(50),
  origin_definition text,
  blend_purpose text,
  source_url text,
  crawled_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kcia_ingredients_code ON kcia_ingredients(ingredient_code);

CREATE TABLE IF NOT EXISTS crawl_state (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source varchar(20) UNIQUE NOT NULL,
  status varchar(20) DEFAULT 'idle',
  total_count int DEFAULT 0,
  processed_count int DEFAULT 0,
  last_ingredient_code varchar(20),
  error_message text,
  started_at timestamptz,
  ended_at timestamptz
);
