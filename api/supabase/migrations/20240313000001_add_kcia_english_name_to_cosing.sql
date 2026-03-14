-- cosing_ingredients 테이블에 kcia_english_name 컬럼 추가
-- (이전에 IF NOT EXISTS로 테이블이 이미 생성된 경우 누락될 수 있음)

ALTER TABLE cosing_ingredients ADD COLUMN IF NOT EXISTS kcia_english_name text;

-- 인덱스가 없는 경우에만 생성 (동일 인덱스 재생성 방지)
CREATE INDEX IF NOT EXISTS idx_cosing_ingredients_kcia_english_name ON cosing_ingredients(kcia_english_name);
