import { useQuery } from "@tanstack/react-query";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from "recharts";
import { getDashboardStats } from "../lib/api";
import { formatNum, PLATFORM_LABELS, MODULE_META } from "../lib/utils";
import StatCard from "../components/StatCard";
import ReportCard from "../components/ReportCard";

const PIE_COLORS = ["#ff2442", "#a855f7", "#ff4500", "#4285f4", "#22c55e"];

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 text-sm">加载中...</div>
      </div>
    );
  }

  const platformData = Object.entries(stats?.platform_distribution || {}).map(([k, v]) => ({
    name: PLATFORM_LABELS[k] || k,
    value: v,
  }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">总览</h1>
        <p className="text-gray-500 text-sm mt-1">TrendSee — 数据故事自动化运营系统</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="采集条目" value={formatNum(stats?.total_items || 0)} icon="📥" sub="原始数据总量" />
        <StatCard label="生成报告" value={stats?.total_reports || 0} icon="📊" sub="各模块报告" />
        <StatCard label="生成内容" value={stats?.total_content || 0} icon="✍️" sub="XHS + 公众号" />
        <StatCard label="执行任务" value={stats?.total_jobs || 0} icon="⚙️" sub="采集 & 分析" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Platform distribution */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">数据来源分布</h3>
          {platformData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={platformData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {platformData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                  labelStyle={{ color: "#6b7280" }}
                  itemStyle={{ color: "#111827" }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-gray-300 text-sm">
              暂无数据 — 请先运行采集任务
            </div>
          )}
          <div className="flex flex-wrap gap-3 mt-3">
            {platformData.map((p, i) => (
              <div key={p.name} className="flex items-center gap-1.5 text-xs text-gray-500">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                {p.name} ({formatNum(p.value)})
              </div>
            ))}
          </div>
        </div>

        {/* Module usage */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">模块使用情况</h3>
          <div className="space-y-3">
            {Object.entries(MODULE_META).map(([key, meta]) => {
              const count = stats?.recent_reports?.filter((r) => r.module === key).length || 0;
              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-lg w-7">{meta.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500">{meta.label}</span>
                      <span className="text-xs text-gray-400">{count} 期</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-brand-500 to-purple-500 rounded-full transition-all"
                        style={{ width: `${Math.min(count * 20, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent reports */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-4">最近报告</h3>
        {stats?.recent_reports?.length ? (
          <div className="space-y-3">
            {stats.recent_reports.map((r) => (
              <ReportCard key={r.id} report={r} />
            ))}
          </div>
        ) : (
          <div className="card text-center text-gray-400 text-sm py-12">
            暂无报告 — 从左侧模块开始运行吧 🚀
          </div>
        )}
      </div>
    </div>
  );
}
