"use client";

import { useState, useCallback, useEffect } from "react";
import { CrawlerCard } from "@/components/admin/ingredient-crawler/CrawlerCard";
import type { CrawlSource, CrawlState } from "@/lib/ingredient-crawler-types";
import { INITIAL_CRAWL_STATE } from "@/lib/ingredient-crawler-types";
import {
  startKciaCrawl,
  abortKciaCrawl,
  getKciaStatus,
  startCosingCrawl,
  abortCosingCrawl,
  getCosingStatus,
  checkApiHealth,
  type KciaStatus,
  type CosingStatus,
} from "@/lib/api";

function kciaStatusToState(s: KciaStatus): CrawlState {
  const status = s.status as CrawlState["status"];
  return {
    startedAt: s.started_at,
    endedAt: s.ended_at,
    extractedAt: s.ended_at ?? s.started_at,
    status,
    result:
      status === "success"
        ? `성공: ${s.processed_count}건`
        : status === "error"
          ? s.error_message ?? "오류 발생"
          : status === "aborted"
            ? `중단됨: ${s.processed_count}건 처리됨`
            : null,
    count: s.processed_count,
    totalCount: s.total_count,
    processedCount: s.processed_count,
    error: s.error_message,
    data: [],
  };
}

function cosingStatusToState(s: CosingStatus): CrawlState {
  const status = s.status as CrawlState["status"];
  return {
    startedAt: s.started_at,
    endedAt: s.ended_at,
    extractedAt: s.ended_at ?? s.started_at,
    status,
    result:
      status === "success"
        ? `성공: ${s.processed_count}건`
        : status === "error"
          ? s.error_message ?? "오류 발생"
          : status === "aborted"
            ? `중단됨: ${s.processed_count}건 처리됨`
            : null,
    count: s.processed_count,
    totalCount: s.total_count,
    processedCount: s.processed_count,
    currentSearchKeyword: s.current_search_keyword,
    currentSearchResultCount: s.current_search_result_count,
    error: s.error_message,
    data: [],
  };
}

const SERVER_CHECK_INTERVAL_MS = 15000;

export default function IngredientCrawlerPage() {
  const [kciaState, setKciaState] = useState<CrawlState>(INITIAL_CRAWL_STATE);
  const [cosingState, setCosingState] = useState<CrawlState>(INITIAL_CRAWL_STATE);
  const [kciaServerConnected, setKciaServerConnected] = useState<
    boolean | null
  >(null);
  const [cosingServerConnected, setCosingServerConnected] = useState<
    boolean | null
  >(null);

  /** API 서버 연결 여부 확인 - Kcia/CosIng 모두 동일 백엔드 사용 */
  const checkApiServer = useCallback(async () => {
    const ok = await checkApiHealth();
    setKciaServerConnected(ok);
    setCosingServerConnected(ok);
    return ok;
  }, []);

  const fetchKciaStatus = useCallback(async () => {
    try {
      const s = await getKciaStatus();
      setKciaState(kciaStatusToState(s));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "API 연결 실패";
      setKciaState((prev) => ({ ...prev, error: msg }));
    }
  }, []);

  const fetchCosingStatus = useCallback(async () => {
    try {
      const s = await getCosingStatus();
      setCosingState(cosingStatusToState(s));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "API 연결 실패";
      setCosingState((prev) => ({ ...prev, error: msg }));
    }
  }, []);

  useEffect(() => {
    fetchKciaStatus();
  }, [fetchKciaStatus]);

  useEffect(() => {
    fetchCosingStatus();
  }, [fetchCosingStatus]);

  useEffect(() => {
    checkApiServer();
    const interval = setInterval(checkApiServer, SERVER_CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [checkApiServer]);

  useEffect(() => {
    if (kciaState.status !== "running") return;
    const interval = setInterval(fetchKciaStatus, 2000);
    return () => clearInterval(interval);
  }, [kciaState.status, fetchKciaStatus]);

  useEffect(() => {
    if (cosingState.status !== "running") return;
    const interval = setInterval(fetchCosingStatus, 2000);
    return () => clearInterval(interval);
  }, [cosingState.status, fetchCosingStatus]);

  const handleStart = useCallback(
    (source: CrawlSource, resume: boolean = false) => {
      if (source === "kcia") {
        setKciaState((prev) => ({
          ...prev,
          status: "running",
          result: null,
          error: null,
        }));
        startKciaCrawl(resume)
          .then(() => fetchKciaStatus())
          .catch((err) => {
            setKciaState((prev) => ({
              ...prev,
              status: "error",
              error: err.message ?? "시작 실패",
            }));
          });
      } else if (source === "cosing") {
        setCosingState((prev) => ({
          ...prev,
          status: "running",
          result: null,
          error: null,
        }));
        startCosingCrawl(resume)
          .then(() => fetchCosingStatus())
          .catch((err) => {
            setCosingState((prev) => ({
              ...prev,
              status: "error",
              error: err.message ?? "시작 실패",
            }));
          });
      }
    },
    [fetchKciaStatus, fetchCosingStatus]
  );

  const handleAbort = useCallback(
    (source: CrawlSource) => {
      if (source === "kcia") {
        abortKciaCrawl()
          .then(() => fetchKciaStatus())
          .catch((err) => {
            setKciaState((prev) => ({
              ...prev,
              error: err.message ?? "중단 요청 실패",
            }));
          });
      } else if (source === "cosing") {
        abortCosingCrawl()
          .then(() => fetchCosingStatus())
          .catch((err) => {
            setCosingState((prev) => ({
              ...prev,
              error: err.message ?? "중단 요청 실패",
            }));
          });
      }
    },
    [fetchKciaStatus, fetchCosingStatus]
  );

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-100">성분정보 크롤러</h1>
      <p className="mt-2 text-slate-400">
        성분 사전 데이터를 크롤링하고 다운로드합니다.
      </p>

      <div className="mt-8 space-y-6">
        <CrawlerCard
          title="대한화장품협회 성분사전"
          source="kcia"
          state={kciaState}
          onStart={() => handleStart("kcia", false)}
          onResume={() => handleStart("kcia", true)}
          onAbort={() => handleAbort("kcia")}
          useApiDownload
          serverConnected={kciaServerConnected}
        />
        <CrawlerCard
          title="CosIng"
          source="cosing"
          state={cosingState}
          onStart={() => handleStart("cosing", false)}
          onResume={() => handleStart("cosing", true)}
          onAbort={() => handleAbort("cosing")}
          useApiDownload
          serverConnected={cosingServerConnected}
        />
      </div>
    </div>
  );
}
