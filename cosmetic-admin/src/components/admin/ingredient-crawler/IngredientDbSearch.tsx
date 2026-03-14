"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  searchKciaIngredients,
  searchCosingIngredients,
  type KciaIngredientRecord,
  type CosingIngredientRecord,
} from "@/lib/api";

const DEBOUNCE_MS = 350;
const DEFAULT_LIMIT = 50;

function truncate(str: string | undefined | null, maxLen: number): string {
  if (str == null || str === "") return "-";
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + "…";
}

export function IngredientDbSearch() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const [kciaResults, setKciaResults] = useState<KciaIngredientRecord[]>([]);
  const [cosingResults, setCosingResults] = useState<CosingIngredientRecord[]>([]);
  const [kciaLoading, setKciaLoading] = useState(false);
  const [cosingLoading, setCosingLoading] = useState(false);
  const [kciaError, setKciaError] = useState<string | null>(null);
  const [cosingError, setCosingError] = useState<string | null>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [query]);

  const searchIdRef = useRef(0);

  const doSearch = useCallback(async (q: string) => {
    if (!q) {
      setKciaResults([]);
      setCosingResults([]);
      setKciaError(null);
      setCosingError(null);
      return;
    }

    const id = ++searchIdRef.current;
    setKciaLoading(true);
    setCosingLoading(true);
    setKciaError(null);
    setCosingError(null);

    const [kciaResult, cosingResult] = await Promise.allSettled([
      searchKciaIngredients(q, DEFAULT_LIMIT),
      searchCosingIngredients(q, DEFAULT_LIMIT),
    ]);

    if (id !== searchIdRef.current) return;

    setKciaResults(kciaResult.status === "fulfilled" ? kciaResult.value : []);
    setCosingResults(cosingResult.status === "fulfilled" ? cosingResult.value : []);

    setKciaError(
      kciaResult.status === "rejected"
        ? (kciaResult.reason instanceof Error ? kciaResult.reason.message : String(kciaResult.reason))
        : null
    );
    setCosingError(
      cosingResult.status === "rejected"
        ? (cosingResult.reason instanceof Error ? cosingResult.reason.message : String(cosingResult.reason))
        : null
    );

    setKciaLoading(false);
    setCosingLoading(false);
  }, []);

  useEffect(() => {
    if (debouncedQuery) {
      doSearch(debouncedQuery);
    } else {
      setKciaResults([]);
      setCosingResults([]);
      setKciaError(null);
      setCosingError(null);
    }
  }, [debouncedQuery, doSearch]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      setDebouncedQuery(query.trim());
    }
  };

  const hasSearched = debouncedQuery.length > 0;
  const showEmptyState = hasSearched && !kciaLoading && !cosingLoading;

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-6">
      <h2 className="mb-4 text-lg font-semibold text-slate-100">성분 DB 조회</h2>

      <div className="mb-6">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="성분명, INCI명, CAS 번호 등으로 검색"
          className="w-full max-w-md rounded-lg border border-slate-600 bg-slate-800 px-4 py-2.5 text-slate-100 placeholder-slate-500 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
          aria-label="성분 검색"
        />
      </div>

      {!hasSearched && (
        <p className="text-sm text-slate-500">
          검색어를 입력하면 대한화장품협회 성분사전과 CosIng DB에서 동시에 조회됩니다.
        </p>
      )}

      {showEmptyState &&
        kciaResults.length === 0 &&
        cosingResults.length === 0 &&
        !kciaError &&
        !cosingError && (
          <p className="text-sm text-slate-500">검색 결과가 없습니다.</p>
        )}

      {(kciaError || cosingError) && (
        <p className="mb-4 text-sm text-red-400">{kciaError || cosingError}</p>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* KCA 결과 */}
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-300">
            대한화장품협회 성분사전
            {kciaLoading && (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-500 border-t-transparent" aria-hidden />
            )}
            {!kciaLoading && hasSearched && (
              <span className="text-slate-500">({kciaResults.length}건)</span>
            )}
          </h3>
          <div className="max-h-[400px] overflow-auto rounded-lg border border-slate-700 bg-slate-900/50">
            {kciaResults.length === 0 && !kciaLoading ? (
              <div className="p-4 text-center text-sm text-slate-500">결과 없음</div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-slate-800 text-xs text-slate-500">
                  <tr>
                    <th className="p-2 font-medium">코드</th>
                    <th className="p-2 font-medium">한글명</th>
                    <th className="p-2 font-medium">영문명</th>
                    <th className="p-2 font-medium">CAS</th>
                    <th className="p-2 font-medium">혼합목적</th>
                  </tr>
                </thead>
                <tbody>
                  {kciaResults.map((row, i) => (
                    <tr key={row.ingredient_code ?? row.id ?? i} className="border-t border-slate-700/50">
                      <td className="p-2 font-mono text-slate-300">{row.ingredient_code ?? "-"}</td>
                      <td className="p-2 text-slate-300">{truncate(row.ingredient_name, 30)}</td>
                      <td className="p-2 text-slate-300">{truncate(row.english_name, 25)}</td>
                      <td className="p-2 font-mono text-slate-400">{row.cas_number ?? "-"}</td>
                      <td className="p-2 text-slate-400">{truncate(row.blend_purpose, 20)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* CosIng 결과 */}
        <div>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-300">
            CosIng
            {cosingLoading && (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-500 border-t-transparent" aria-hidden />
            )}
            {!cosingLoading && hasSearched && (
              <span className="text-slate-500">({cosingResults.length}건)</span>
            )}
          </h3>
          <div className="max-h-[400px] overflow-auto rounded-lg border border-slate-700 bg-slate-900/50">
            {cosingResults.length === 0 && !cosingLoading ? (
              <div className="p-4 text-center text-sm text-slate-500">결과 없음</div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-slate-800 text-xs text-slate-500">
                  <tr>
                    <th className="p-2 font-medium">INCI명</th>
                    <th className="p-2 font-medium">설명</th>
                    <th className="p-2 font-medium">CAS</th>
                    <th className="p-2 font-medium">기능</th>
                  </tr>
                </thead>
                <tbody>
                  {cosingResults.map((row, i) => (
                    <tr key={row.inci_name ?? row.id ?? i} className="border-t border-slate-700/50">
                      <td className="p-2 font-mono text-slate-300">{truncate(row.inci_name, 25)}</td>
                      <td className="p-2 text-slate-300">{truncate(row.description, 40)}</td>
                      <td className="p-2 font-mono text-slate-400">{row.cas_number ?? "-"}</td>
                      <td className="p-2 text-slate-400">{truncate(row.functions, 25)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
