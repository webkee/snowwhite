-- crawl_state에 추출 중단 요청 플래그 추가

ALTER TABLE crawl_state
ADD COLUMN IF NOT EXISTS abort_requested boolean DEFAULT false;
