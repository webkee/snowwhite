import type { LucideIcon } from "lucide-react";
import {
  Database,
  Package,
  MessagesSquare,
  Layout,
  FlaskConical,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export interface AdminMenuItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const ADMIN_MENUS: AdminMenuItem[] = [
  { href: "/admin/ingredient-crawler", label: "성분정보 크롤러", icon: Database },
  { href: "/admin/product-crawler", label: "제품 전성분 크롤러", icon: Package },
  { href: "/admin/review-crawler", label: "상품리뷰 크롤러", icon: MessagesSquare },
  {
    href: "/admin/ad-copy-crawler",
    label: "상세페이지 광고문안 크롤러",
    icon: Layout,
  },
  {
    href: "/admin/formulation-create",
    label: "화장품 카테고리별 처방 생성",
    icon: FlaskConical,
  },
  { href: "/admin/ra-review", label: "생성된 처방 RA검토", icon: ShieldCheck },
  {
    href: "/admin/ad-copy-generate",
    label: "처방 기준 광고문안 생성",
    icon: Sparkles,
  },
];
