-- cosing_ingredients에 누락된 컬럼 보정
-- (테이블이 다른 경로로 생성된 경우 PGRST204 오류 방지)

ALTER TABLE cosing_ingredients ADD COLUMN IF NOT EXISTS cosmetics_regulation_provisions text;
ALTER TABLE cosing_ingredients ADD COLUMN IF NOT EXISTS identified_ingredients text;
ALTER TABLE cosing_ingredients ADD COLUMN IF NOT EXISTS functions text;
ALTER TABLE cosing_ingredients ADD COLUMN IF NOT EXISTS sccs_opinions text;
