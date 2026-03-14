"use client";

import type { CrawlStatus } from "@/lib/ingredient-crawler-types";

const STATUS_LABELS: Record<CrawlStatus, string> = {
  idle: "대기",
  running: "추출 중",
  success: "완료",
  error: "오류",
  aborted: "중단됨",
};

const STATUS_STYLES: Record<
  CrawlStatus,
  { bg: string; text: string; border: string }
> = {
  idle: { bg: "bg-slate-700/50", text: "text-slate-400", border: "border-slate-600" },
  running: { bg: "bg-amber-500/20", text: "text-amber-400", border: "border-amber-500/50" },
  success: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/50" },
  error: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/50" },
  aborted: { bg: "bg-orange-500/20", text: "text-orange-400", border: "border-orange-500/50" },
};

interface StatusBadgeProps {
  status: CrawlStatus;
  showSpinner?: boolean;
}

export function StatusBadge({ status, showSpinner = false }: StatusBadgeProps) {
  const style = STATUS_STYLES[status];
  const label = STATUS_LABELS[status];

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-xs font-medium ${style.bg} ${style.text} ${style.border}`}
      role="status"
    >
      {showSpinner && status === "running" && (
        <span
          className="h-3 w-3 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent"
          aria-hidden
        />
      )}
      {label}
    </span>
  );
}
