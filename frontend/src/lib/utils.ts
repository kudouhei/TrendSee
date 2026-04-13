import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNum(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}w`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const PLATFORM_COLORS: Record<string, string> = {
  xhs: "#ff2442",
  douyin: "#010101",
  reddit: "#ff4500",
  google_trends: "#4285f4",
};

export const PLATFORM_LABELS: Record<string, string> = {
  xhs: "小红书",
  douyin: "抖音",
  reddit: "Reddit",
  google_trends: "Google趋势",
};

export const MODULE_META: Record<string, { label: string; icon: string; color: string }> = {
  trend_radar:    { label: "趋势雷达",   icon: "📡", color: "text-blue-600" },
  comment_mining: { label: "评论区挖矿", icon: "⛏️", color: "text-amber-600" },
  viral_anatomy:  { label: "爆款解剖室", icon: "🔬", color: "text-rose-600" },
  vertical_deep:  { label: "垂直精分",   icon: "🎯", color: "text-emerald-600" },
};

export const PHASE_COLORS: Record<string, string> = {
  rising:   "bg-green-50 text-green-700 border border-green-200",
  peak:     "bg-amber-50 text-amber-700 border border-amber-200",
  declining:"bg-red-50 text-red-700 border border-red-200",
  stable:   "bg-blue-50 text-blue-700 border border-blue-200",
  unknown:  "bg-gray-100 text-gray-500 border border-gray-200",
};

export const PHASE_LABELS: Record<string, string> = {
  rising: "上升期", peak: "爆发期", declining: "衰退期", stable: "稳定期", unknown: "未知",
};
