-- character varying(20) 초과 오류 수정
-- CosIng 크롤러는 last_ingredient_code에 english_name을 저장하는데, 성분명이 20자를 초과할 수 있음

ALTER TABLE crawl_state
  ALTER COLUMN last_ingredient_code TYPE text;
