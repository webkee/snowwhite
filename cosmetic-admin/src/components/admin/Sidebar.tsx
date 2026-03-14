"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ADMIN_MENUS } from "@/lib/admin-menu";

/**
 * 데스크톱용 고정 사이드바.
 * 모바일에서는 숨겨지고 MobileSidebar가 대신 표시됨.
 */
export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="fixed left-0 top-0 z-40 hidden h-screen w-64 flex-col border-r border-slate-700 bg-slate-900 md:flex"
      aria-label="관리자 메뉴"
    >
      <div className="flex h-14 items-center border-b border-slate-700 px-6">
        <Link
          href="/admin"
          className="text-lg font-semibold text-zinc-200 transition-colors hover:text-white"
        >
          화장품 개발 시스템
        </Link>
      </div>
      <nav className="flex-1 overflow-y-auto p-3">
        <ul className="space-y-1" role="menubar">
          {ADMIN_MENUS.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <li key={href} role="none">
                <Link
                  href={href}
                  role="menuitem"
                  className={`flex min-h-[44px] items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                    isActive
                      ? "bg-slate-800 text-zinc-200"
                      : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                  }`}
                >
                  <Icon
                    className="h-5 w-5 shrink-0"
                    aria-hidden
                  />
                  <span className="truncate">{label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
