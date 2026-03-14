"use client";

import type { CrawlSource, CrawlState } from "@/lib/ingredient-crawler-types";
import { StatusBadge } from "./StatusBadge";
import {
  downloadAsJSON,
  downloadAsCSV,
  downloadFromApiAsJson,
  downloadFromApiAsCsv,
} from "./download-utils";
import {
  getKciaExportJsonUrl,
  getKciaExportCsvUrl,
  getCosingExportJsonUrl,
  getCosingExportCsvUrl,
  getOliveSkincareExportCsvUrl,
  getOliveMakeupExportCsvUrl,
} from "@/lib/api";

/** 서버 연결 상태: true=연결됨, false=끊김, null=확인중, undefined=API 미구현 */
export type ServerConnectionStatus = boolean | null | undefined;

interface CrawlerCardProps {
  title: string;
  source: CrawlSource;
  state: CrawlState;
  onStart: () => void;
  onResume?: () => void;
  /** 추출 중단 핸들러 (running 상태에서만 노출) */
  onAbort?: () => void;
  /** true면 API export URL 사용 (DB 데이터) */
  useApiDownload?: boolean;
  /** API 서버 연결 상태 (undefined = 해당 소스 API 미구현) */
  serverConnected?: ServerConnectionStatus;
}

function ServerStatusIndicator({ status }: { status: ServerConnectionStatus }) {
  if (status === undefined) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
        <span className="h-1.5 w-1.5 rounded-full bg-slate-500" aria-hidden />
        준비중
      </span>
    );
  }
  if (status === null) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-slate-400">
        <span
          className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-500"
          aria-hidden
        />
        확인 중
      </span>
    );
  }
  if (status) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
        <span
          className="h-1.5 w-1.5 rounded-full bg-emerald-500"
          aria-hidden
          title="API 서버 연결됨"
        />
        연결됨
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-red-400">
      <span
        className="h-1.5 w-1.5 rounded-full bg-red-500"
        aria-hidden
        title="API 서버 연결 끊김"
      />
      연결 끊김
    </span>
  );
}

function formatDateTime(s: string | null): string {
  if (!s) return "-";
  const d = new Date(s);
  return d.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(s: string | null): string {
  if (!s) return "-";
  const d = new Date(s);
  return d.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function CrawlerCard({
  title,
  source,
  state,
  onStart,
  onResume,
  onAbort,
  useApiDownload = false,
  serverConnected,
}: CrawlerCardProps) {
  const hasData = state.data.length > 0;
  const isOlive = source === "olive_skincare" || source === "olive_makeup";
  const sourceName =
    source === "kcia"
      ? "kcia"
      : source === "cosing"
        ? "cosing"
        : source === "olive_skincare"
          ? "olive_skincare"
          : "olive_makeup";
  const canDownload = useApiDownload || hasData;
  const showJsonButton = !isOlive;
  /** 진행률 (%) - total이 알려진 경우에만 유효 */
  const progress =
    state.totalCount != null &&
    state.processedCount != null &&
    state.totalCount > 0
      ? Math.round((state.processedCount / state.totalCount) * 100)
      : null;
  /** 추출 진행 중 여부 (progress 유무와 무관) */
  const isExtracting = state.status === "running";

  const handleJsonDownload = () => {
    if (useApiDownload && source === "kcia") {
      downloadFromApiAsJson(getKciaExportJsonUrl(), sourceName).catch((err) =>
        console.error("JSON 다운로드 실패:", err)
      );
    } else if (useApiDownload && source === "cosing") {
      downloadFromApiAsJson(getCosingExportJsonUrl(), sourceName).catch((err) =>
        console.error("JSON 다운로드 실패:", err)
      );
    } else if (hasData) {
      downloadAsJSON(state.data, sourceName);
    }
  };

  const handleCsvDownload = () => {
    if (useApiDownload && source === "kcia") {
      downloadFromApiAsCsv(getKciaExportCsvUrl(), sourceName).catch((err) =>
        console.error("CSV 다운로드 실패:", err)
      );
    } else if (useApiDownload && source === "cosing") {
      downloadFromApiAsCsv(getCosingExportCsvUrl(), sourceName).catch((err) =>
        console.error("CSV 다운로드 실패:", err)
      );
    } else if (useApiDownload && source === "olive_skincare") {
      downloadFromApiAsCsv(
        getOliveSkincareExportCsvUrl(),
        sourceName
      ).catch((err) => console.error("CSV 다운로드 실패:", err));
    } else if (useApiDownload && source === "olive_makeup") {
      downloadFromApiAsCsv(getOliveMakeupExportCsvUrl(), sourceName).catch(
        (err) => console.error("CSV 다운로드 실패:", err)
      );
    } else if (hasData) {
      downloadAsCSV(state.data, sourceName);
    }
  };

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
        <div className="flex items-center gap-3">
          <ServerStatusIndicator status={serverConnected} />
          <StatusBadge status={state.status} showSpinner />
        </div>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <p className="text-xs text-slate-500">추출시작</p>
          <p className="mt-0.5 font-mono text-sm text-slate-300">
            {formatDateTime(state.startedAt)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">추출종료</p>
          <p className="mt-0.5 font-mono text-sm text-slate-300">
            {formatDateTime(state.endedAt)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">추출일자</p>
          <p className="mt-0.5 font-mono text-sm text-slate-300">
            {formatDate(state.extractedAt)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">추출결과</p>
          <p className="mt-0.5 text-sm text-slate-300">
            {state.status === "running" && (
              <>
                {progress != null ? `${progress}% (${state.processedCount}/${state.totalCount})` : "추출 중..."}
              </>
            )}
            {state.status === "success" && state.result}
            {state.status === "error" && (
              <span className="text-red-400">{state.error ?? state.result}</span>
            )}
            {state.status === "aborted" && (
              <span className="text-orange-400">
                {state.result ?? "사용자에 의해 중단됨"}
              </span>
            )}
            {state.status === "idle" && "-"}
          </p>
        </div>
      </div>

      {/* 추출 진행바: running 시 항상 표시 (total 미확정이면 무한 진행 애니메이션) */}
      {(isExtracting || (state.status === "aborted" && progress != null)) && (
        <div className="mb-5">
          <div className="mb-1.5 flex items-center justify-between text-xs">
            <span className="text-slate-400">
              {isExtracting
                ? progress != null
                  ? `추출 중... ${state.processedCount} / ${state.totalCount}건`
                  : source === "cosing"
                    ? state.currentSearchKeyword != null ||
                        state.currentSearchResultCount != null
                      ? `검색어 '${state.currentSearchKeyword ?? "-"}': ${state.currentSearchResultCount ?? 0}건 검색됨, ${state.processedCount ?? 0}건 추출 중`
                      : "검색 준비 중..."
                    : "추출 준비 중... (목록 수집)"
                : "중단됨"}
            </span>
            {progress != null && (
              <span className="font-mono text-slate-300">{progress}%</span>
            )}
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-700">
            {progress != null ? (
              <div
                className="h-full bg-emerald-500 transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              />
            ) : (
              <div
                className="animate-progress-indeterminate h-full w-1/3 rounded-full bg-emerald-500/80"
                aria-hidden
              />
            )}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => onStart()}
          disabled={state.status === "running"}
          className="inline-flex items-center gap-2 rounded-lg bg-slate-600 px-4 py-2.5 text-sm font-medium text-slate-100 transition-colors hover:bg-slate-600/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {state.status === "running" && (
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
              aria-hidden
            />
          )}
          추출 시작
        </button>
        {onAbort != null && state.status === "running" && (
          <button
            type="button"
            onClick={() => onAbort()}
            className="inline-flex items-center gap-2 rounded-lg border border-orange-500/50 bg-orange-500/20 px-4 py-2.5 text-sm font-medium text-orange-400 transition-colors hover:bg-orange-500/30"
          >
            추출 중단
          </button>
        )}
        {onResume != null && (
          <button
            type="button"
            onClick={() => onResume()}
            disabled={state.status === "running"}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-800 px-4 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            이어받기
          </button>
        )}
        {showJsonButton && (
          <button
            type="button"
            onClick={handleJsonDownload}
            disabled={!canDownload}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-800 px-4 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            JSON 다운로드
          </button>
        )}
        <button
          type="button"
          onClick={handleCsvDownload}
          disabled={!canDownload}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-800 px-4 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          CSV 다운로드
        </button>
      </div>
    </div>
  );
}
