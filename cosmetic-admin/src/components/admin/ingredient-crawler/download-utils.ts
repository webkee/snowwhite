/**
 * JSON/CSV 다운로드 유틸리티
 */

import type { IngredientItem } from "@/lib/ingredient-crawler-types";

const HEADERS = [
  "ingredient_code",
  "ingredient_name",
  "old_name",
  "english_name",
  "cas_number",
  "origin_definition",
  "blend_purpose",
  "source_url",
  "crawled_at",
] as const;

/**
 * 객체 배열을 CSV 문자열로 변환 (KCA 스키마 지원)
 */
export function objectsToCSV(rows: IngredientItem[]): string {
  if (rows.length === 0) return "";

  const escape = (val: string | undefined): string => {
    if (val == null || val === "") return "";
    const s = String(val);
    if (s.includes(",") || s.includes('"') || s.includes("\n")) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };

  const headerRow = [...HEADERS].join(",");
  const dataRows = rows.map((row) => {
    const r = row as Record<string, unknown>;
    return HEADERS.map((h) => escape(r[h] as string | undefined)).join(",");
  });

  return [headerRow, ...dataRows].join("\n");
}

/**
 * Blob을 이용해 파일 다운로드
 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * JSON 파일로 다운로드 (로컬 데이터)
 */
export function downloadAsJSON(data: IngredientItem[], sourceName: string): void {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const filename = `ingredient-${sourceName}-${formatDateForFilename()}.json`;
  downloadBlob(blob, filename);
}

/**
 * CSV 파일로 다운로드 (로컬 데이터)
 */
export function downloadAsCSV(data: IngredientItem[], sourceName: string): void {
  const csv = objectsToCSV(data);
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
  const filename = `ingredient-${sourceName}-${formatDateForFilename()}.csv`;
  downloadBlob(blob, filename);
}

/**
 * API URL에서 JSON 다운로드
 */
export async function downloadFromApiAsJson(
  apiUrl: string,
  sourceName: string
): Promise<void> {
  const res = await fetch(apiUrl);
  if (!res.ok) throw new Error("다운로드 실패");
  const blob = await res.blob();
  const filename = `ingredient-${sourceName}-${formatDateForFilename()}.json`;
  downloadBlob(blob, filename);
}

/**
 * API URL에서 CSV 다운로드
 */
export async function downloadFromApiAsCsv(
  apiUrl: string,
  sourceName: string
): Promise<void> {
  const res = await fetch(apiUrl);
  if (!res.ok) throw new Error("다운로드 실패");
  const blob = await res.blob();
  const filename = `ingredient-${sourceName}-${formatDateForFilename()}.csv`;
  downloadBlob(blob, filename);
}

function formatDateForFilename(): string {
  const now = new Date();
  return now.toISOString().slice(0, 19).replace(/[-:T]/g, "");
}
