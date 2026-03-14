"use client";

import { useState, useCallback, useEffect } from "react";
import { CrawlerCard } from "@/components/admin/ingredient-crawler/CrawlerCard";
import type { CrawlSource, CrawlState } from "@/lib/ingredient-crawler-types";
import { INITIAL_CRAWL_STATE } from "@/lib/ingredient-crawler-types";
import {
  startOliveSkincareCrawl,
  startOliveMakeupCrawl,
  checkApiHealth,
} from "@/lib/api";

const SERVER_CHECK_INTERVAL_MS = 15000;

export default function ProductCrawlerPage() {
  const [oliveSkincareState, setOliveSkincareState] =
    useState<CrawlState>(INITIAL_CRAWL_STATE);
  const [oliveMakeupState, setOliveMakeupState] =
    useState<CrawlState>(INITIAL_CRAWL_STATE);
  const [serverConnected, setServerConnected] = useState<boolean | null>(null);

  const checkApiServer = useCallback(async () => {
    const ok = await checkApiHealth();
    setServerConnected(ok);
    return ok;
  }, []);

  useEffect(() => {
    checkApiServer();
    const interval = setInterval(checkApiServer, SERVER_CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [checkApiServer]);

  const handleStart = useCallback(
    (source: CrawlSource) => {
      if (source === "olive_skincare") {
        setOliveSkincareState((prev) => ({
          ...prev,
          status: "running",
          result: null,
          error: null,
        }));
        startOliveSkincareCrawl()
          .then(() => {
            setOliveSkincareState((prev) => ({
              ...prev,
              status: "success",
              result: "백그라운드에서 크롤이 시작되었습니다. 완료 후 CSV 다운로드가 가능합니다.",
              startedAt: new Date().toISOString(),
              extractedAt: new Date().toISOString(),
            }));
          })
          .catch((err) => {
            setOliveSkincareState((prev) => ({
              ...prev,
              status: "error",
              error: err instanceof Error ? err.message : "시작 실패",
            }));
          });
      } else if (source === "olive_makeup") {
        setOliveMakeupState((prev) => ({
          ...prev,
          status: "running",
          result: null,
          error: null,
        }));
        startOliveMakeupCrawl()
          .then(() => {
            setOliveMakeupState((prev) => ({
              ...prev,
              status: "success",
              result: "백그라운드에서 크롤이 시작되었습니다. 완료 후 CSV 다운로드가 가능합니다.",
              startedAt: new Date().toISOString(),
              extractedAt: new Date().toISOString(),
            }));
          })
          .catch((err) => {
            setOliveMakeupState((prev) => ({
              ...prev,
              status: "error",
              error: err instanceof Error ? err.message : "시작 실패",
            }));
          });
      }
    },
    []
  );

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-100">
        제품 전성분 크롤러
      </h1>
      <p className="mt-2 text-slate-400">
        제품의 전성분 및 상품정보 제공고시를 크롤링합니다.
      </p>

      <div className="mt-8 space-y-6">
        <CrawlerCard
          title="올리브영 스킨케어"
          source="olive_skincare"
          state={oliveSkincareState}
          onStart={() => handleStart("olive_skincare")}
          useApiDownload
          serverConnected={serverConnected}
        />
        <CrawlerCard
          title="올리브영 메이크업"
          source="olive_makeup"
          state={oliveMakeupState}
          onStart={() => handleStart("olive_makeup")}
          useApiDownload
          serverConnected={serverConnected}
        />
      </div>
    </div>
  );
}
