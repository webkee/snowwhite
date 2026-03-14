-- character varying(50) 초과 오류 수정
-- CAS/EC 번호가 복수 개 연결되거나 긴 형식일 때 50자 초과 가능

-- cosing_ingredients
ALTER TABLE cosing_ingredients
  ALTER COLUMN cas_number TYPE text,
  ALTER COLUMN ec_number TYPE text;

-- kcia_ingredients
ALTER TABLE kcia_ingredients
  ALTER COLUMN cas_number TYPE text;
