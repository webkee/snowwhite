"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { X } from "lucide-react";
import { ADMIN_MENUS } from "@/lib/admin-menu";
import { useSidebar } from "./SidebarContext";

/**
 * 모바일용 오버레이 사이드바.
 * 햄버거 메뉴 클릭 시 슬라이드로 표시됨.
 */
export function MobileSidebar() {
  const pathname = usePathname();
  const { isOpen, close } = useSidebar();

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
    }
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, close]);

  useEffect(() => {
    close();
  }, [pathname, close]);

  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/50 md:hidden"
        onClick={close}
        aria-hidden
      />
      <aside
        className="fixed inset-y-0 left-0 z-50 w-64 translate-x-0 flex-col border-r border-slate-700 bg-slate-900 shadow-xl transition-transform duration-200 ease-out md:hidden md:translate-x-[-100%]"
        aria-label="관리자 메뉴"
        aria-modal="true"
      >
        <div className="flex h-14 items-center justify-between border-b border-slate-700 px-4">
          <Link
            href="/admin"
            className="text-lg font-semibold text-zinc-200"
            onClick={close}
          >
            화장품 개발 시스템
          </Link>
          <button
            type="button"
            onClick={close}
            className="flex h-11 w-11 min-w-[44px] items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-100"
            aria-label="메뉴 닫기"
          >
            <X className="h-6 w-6" aria-hidden />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto p-3">
          <ul className="space-y-1" role="menubar">
            {ADMIN_MENUS.map(({ href, label, icon: Icon }) => {
              const isActive =
                pathname === href || pathname.startsWith(`${href}/`);
              return (
                <li key={href} role="none">
                  <Link
                    href={href}
                    role="menuitem"
                    onClick={close}
                    className={`flex min-h-[44px] items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                      isActive
                        ? "bg-slate-800 text-zinc-200"
                        : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                    }`}
                  >
                    <Icon className="h-5 w-5 shrink-0" aria-hidden />
                    <span className="truncate">{label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>
    </>
  );
}
