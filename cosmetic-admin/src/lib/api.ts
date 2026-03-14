/**
 * API 클라이언트
 */

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface KciaStatus {
  status: string;
  total_count: number;
  processed_count: number;
  last_ingredient_code: string | null;
  error_message: string | null;
  started_at: string | null;
  ended_at: string | null;
}

function wrapFetchError(err: unknown, fallback: string): Error {
  const msg = err instanceof Error ? err.message : String(err);
  if (msg === "Failed to fetch" || msg.includes("NetworkError")) {
    return new Error(
      `${fallback} (API 서버 ${API_BASE} 연결 불가. 서버가 실행 중인지 확인하세요.)`
    );
  }
  return new Error(msg || fallback);
}

/** API 서버 연결 여부 확인 (GET /health) */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function startKciaCrawl(resume: boolean = false): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/crawl/kcia/start?resume=${resume}`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? "크롤 시작 실패");
    }
  } catch (e) {
    throw wrapFetchError(e, "크롤 시작 실패");
  }
}

export async function abortKciaCrawl(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/crawl/kcia/abort`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? "크롤 중단 요청 실패");
    }
  } catch (e) {
    throw wrapFetchError(e, "크롤 중단 요청 실패");
  }
}

export async function getKciaStatus(): Promise<KciaStatus> {
  try {
    const res = await fetch(`${API_BASE}/crawl/kcia/status`);
    if (!res.ok) throw new Error("상태 조회 실패");
    return res.json();
  } catch (e) {
    throw wrapFetchError(e, "상태 조회 실패");
  }
}

export function getKciaExportJsonUrl(): string {
  return `${API_BASE}/crawl/kcia/export/json`;
}

export function getKciaExportCsvUrl(): string {
  return `${API_BASE}/crawl/kcia/export/csv`;
}

// --- CosIng ---

export interface CosingStatus {
  status: string;
  total_count: number;
  processed_count: number;
  last_ingredient_code: string | null;
  current_search_keyword: string | null;
  current_search_result_count: number | null;
  error_message: string | null;
  started_at: string | null;
  ended_at: string | null;
}

export async function startCosingCrawl(resume: boolean = false): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/crawl/cosing/start?resume=${resume}`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? "크롤 시작 실패");
    }
  } catch (e) {
    throw wrapFetchError(e, "크롤 시작 실패");
  }
}

export async function abortCosingCrawl(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/crawl/cosing/abort`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? "크롤 중단 요청 실패");
    }
  } catch (e) {
    throw wrapFetchError(e, "크롤 중단 요청 실패");
  }
}

export async function getCosingStatus(): Promise<CosingStatus> {
  try {
    const res = await fetch(`${API_BASE}/crawl/cosing/status`);
    if (!res.ok) throw new Error("상태 조회 실패");
    return res.json();
  } catch (e) {
    throw wrapFetchError(e, "상태 조회 실패");
  }
}

export function getCosingExportJsonUrl(): string {
  return `${API_BASE}/crawl/cosing/export/json`;
}

export function getCosingExportCsvUrl(): string {
  return `${API_BASE}/crawl/cosing/export/csv`;
}

// --- Olive Young 스킨케어 ---

export async function startOliveSkincareCrawl(
  maxProductsPerCategory?: number
): Promise<void> {
  try {
    const params = new URLSearchParams();
    if (maxProductsPerCategory != null) {
      params.set("max_products_per_category", String(maxProductsPerCategory));
    }
    const query = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${API_BASE}/crawl/olive/start${query}`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? "크롤 시작 실패");
    }
  } catch (e) {
    throw wrapFetchError(e, "크롤 시작 실패");
  }
}

export function getOliveSkincareExportCsvUrl(): string {
  return `${API_BASE}/crawl/olive/export/latest`;
}

// --- Olive Young 메이크업 ---

export async function startOliveMakeupCrawl(
  maxProductsPerCategory?: number
): Promise<void> {
  try {
    const params = new URLSearchParams();
    if (maxProductsPerCategory != null) {
      params.set("max_products_per_category", String(maxProductsPerCategory));
    }
    const query = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${API_BASE}/crawl/olive-makeup/start${query}`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? "크롤 시작 실패");
    }
  } catch (e) {
    throw wrapFetchError(e, "크롤 시작 실패");
  }
}

export function getOliveMakeupExportCsvUrl(): string {
  return `${API_BASE}/crawl/olive-makeup/export/latest`;
}
