-- cosing_id 컬럼 추가 (URL /details/101976 에서 추출)
-- current_search_keyword varchar(50) -> text (긴 검색어 저장)

-- cosing_ingredients: cosing_id 추가 (기존 테이블에 컬럼 있는 경우 스킵)
ALTER TABLE cosing_ingredients ADD COLUMN IF NOT EXISTS cosing_id varchar(50);

-- crawl_state: current_search_keyword가 varchar(50)인 경우 text로 확장
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'crawl_state' AND column_name = 'current_search_keyword'
    AND data_type = 'character varying'
  ) THEN
    ALTER TABLE crawl_state ALTER COLUMN current_search_keyword TYPE text;
  END IF;
END $$;
