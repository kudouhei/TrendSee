import { Link, useLocation } from "react-router-dom";
import { cn } from "../lib/utils";
import {
  LayoutDashboard, Radio, MessageSquare, Microscope, Target,
  Database, FileText, Settings, Zap,
} from "lucide-react";

const NAV = [
  { to: "/",               icon: LayoutDashboard, label: "总览" },
  { to: "/trend-radar",    icon: Radio,           label: "趋势雷达" },
  { to: "/comment-mining", icon: MessageSquare,   label: "评论区挖矿" },
  { to: "/viral-anatomy",  icon: Microscope,      label: "爆款解剖室" },
  { to: "/vertical-deep",  icon: Target,          label: "垂直精分" },
  { to: "/reports",        icon: FileText,        label: "报告库" },
  { to: "/raw-data",       icon: Database,        label: "原始数据" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-700 flex items-center justify-center">
              <Zap size={18} className="text-white" />
            </div>
            <div>
              <p className="font-bold text-gray-900 text-sm leading-none">TrendSee</p>
              <p className="text-gray-400 text-xs mt-0.5">数据故事系统</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV.map(({ to, icon: Icon, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
                pathname === to
                  ? "bg-brand-50 text-brand-700"
                  : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
              )}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-gray-200">
          <Link to="/settings" className="btn-ghost flex items-center gap-3 text-sm w-full">
            <Settings size={16} />
            设置
          </Link>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
