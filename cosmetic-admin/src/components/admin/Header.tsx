"use client";

import { Menu } from "lucide-react";
import { useSidebar } from "./SidebarContext";

/**
 * 상단 고정 헤더.
 * 모바일에서 햄버거 버튼으로 사이드바 열기.
 */
export function Header() {
  const { toggle, isOpen } = useSidebar();

  return (
    <header
      className="fixed right-0 top-0 z-30 flex h-14 items-center justify-between border-b border-slate-700 bg-slate-900/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-slate-900/80 md:left-64"
      role="banner"
    >
      <button
        type="button"
        onClick={toggle}
        className="-ml-2 flex h-11 w-11 min-w-[44px] items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-100 md:hidden"
        aria-label={isOpen ? "메뉴 닫기" : "메뉴 열기"}
        aria-expanded={isOpen}
      >
        <Menu className="h-6 w-6" aria-hidden />
      </button>
      <div className="flex-1 md:ml-0" />
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <span>관리자</span>
      </div>
    </header>
  );
}
