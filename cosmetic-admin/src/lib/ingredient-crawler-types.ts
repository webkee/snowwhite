/**
 * 성분정보 크롤러 관련 타입 정의
 */

/** 크롤링 소스 (대한화장품협회 성분사전 | CosIng | 올리브영) */
export type CrawlSource =
  | "kcia"
  | "cosing"
  | "olive_skincare"
  | "olive_makeup";

/** 크롤링 상태 */
export type CrawlStatus = "idle" | "running" | "success" | "error" | "aborted";

/** 성분 데이터 (크롤링 결과 항목) - KCA 스키마 확장 */
export interface IngredientItem {
  /** @deprecated inciName → ingredient_name */
  inciName?: string;
  ingredient_code?: string;
  ingredient_name?: string;
  old_name?: string;
  englishName?: string;
  english_name?: string;
  casNumber?: string;
  cas_number?: string;
  definition?: string;
  origin_definition?: string;
  blend_purpose?: string;
  source_url?: string;
  crawled_at?: string;
}

/** 크롤링 상태 (사이트별) */
export interface CrawlState {
  startedAt: string | null;
  endedAt: string | null;
  extractedAt: string | null;
  status: CrawlStatus;
  result: string | null;
  count: number;
  totalCount?: number;
  processedCount?: number;
  /** CosIng: 현재 검색어 */
  currentSearchKeyword?: string | null;
  /** CosIng: 현재 검색 결과 수 */
  currentSearchResultCount?: number | null;
  error: string | null;
  data: IngredientItem[];
}

/** 초기 CrawlState */
export const INITIAL_CRAWL_STATE: CrawlState = {
  startedAt: null,
  endedAt: null,
  extractedAt: null,
  status: "idle",
  result: null,
  count: 0,
  error: null,
  data: [],
};
