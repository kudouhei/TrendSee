import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { runTrendRadar } from "../lib/api";
import { PLATFORM_LABELS, PHASE_LABELS, PHASE_COLORS } from "../lib/utils";
import RunButton from "../components/RunButton";
import PlatformBadge from "../components/PlatformBadge";
import PlatformGroupSelector from "../components/PlatformGroupSelector";
import ContentGeneratorPanel from "../components/ContentGeneratorPanel";

const DEFAULT_KEYWORDS = ["AI", "新消费", "出海", "国潮", "社交电商"];
const ALL_PLATFORMS = ["xhs", "douyin", "reddit", "google_trends"];

const TOOLTIP_STYLE = {
  contentStyle: { background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" },
  labelStyle: { color: "#6b7280" },
  itemStyle: { color: "#111827" },
};

type InputMode = "keyword" | "date_range";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}
function sevenDaysAgo() {
  const d = new Date();
  d.setDate(d.getDate() - 7);
  return d.toISOString().slice(0, 10);
}

export default function TrendRadar() {
  const [inputMode, setInputMode] = useState<InputMode>("keyword");
  const [keywords, setKeywords] = useState(DEFAULT_KEYWORDS.join(", "));
  const [dateFrom, setDateFrom] = useState(sevenDaysAgo());
  const [dateTo, setDateTo]     = useState(todayStr());
  const [platforms, setPlatforms] = useState<string[]>(ALL_PLATFORMS);
  const [period, setPeriod] = useState("weekly");
  const [result, setResult] = useState<any>(null);

  const { mutate, isPending } = useMutation({
    mutationFn: runTrendRadar,
    onSuccess: setResult,
  });

  const handleRun = () => {
    if (inputMode === "keyword") {
      mutate({
        keywords: keywords.split(",").map((k) => k.trim()).filter(Boolean),
        platforms,
        period,
        limit_per_source: 20,
      });
    } else {
      mutate({
        keywords: [],
        platforms,
        period: "custom",
        limit_per_source: 20,
        date_from: dateFrom,
        date_to: dateTo,
      });
    }
  };

  const phaseData = result
    ? Object.entries(result.phase_distribution || {}).map(([k, v]) => ({
        name: PHASE_LABELS[k] || k,
        count: v as number,
      }))
    : [];

  const topItems = result?.top_items || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          📡 趋势雷达
        </h1>
        <p className="text-gray-500 text-sm mt-1">跨平台趋势聚合 — 每周/每月捕捉上升信号</p>
      </div>

      {/* Config */}
      <div className="card space-y-4">
        <h3 className="text-sm font-semibold text-gray-900">配置参数</h3>

        {/* Input mode toggle */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 mr-1">输入方式：</span>
          {(["keyword", "date_range"] as InputMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setInputMode(m)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                inputMode === m
                  ? "bg-brand-50 text-brand-700 border-brand-200 font-medium"
                  : "bg-white text-gray-500 border-gray-200 hover:border-gray-300"
              }`}
            >
              {m === "keyword" ? "🔍 关键词" : "📅 日期范围"}
            </button>
          ))}
        </div>

        {/* Keyword input */}
        {inputMode === "keyword" && (
          <div>
            <label className="text-xs text-gray-500 mb-1.5 block">
              关键词（逗号分隔，留空则采集各平台实时热榜）
            </label>
            <input
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900
                         focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 transition-colors"
              placeholder="AI, 新消费, 出海…（留空获取各平台热榜）"
            />
          </div>
        )}

        {/* Date range input */}
        {inputMode === "date_range" && (
          <div>
            <label className="text-xs text-gray-500 mb-1.5 block">
              日期范围（自动采集各平台热点，无需输入关键词）
            </label>
            <div className="flex items-center gap-3">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900
                           focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 transition-colors"
              />
              <span className="text-gray-400 text-xs">至</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900
                           focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 transition-colors"
              />
            </div>
            <p className="text-xs text-gray-400 mt-1.5">
              将采集所选平台当前热榜，并使用日期范围作为 Google Trends 分析时间窗口
            </p>
          </div>
        )}

        {/* Platforms */}
        <PlatformGroupSelector selected={platforms} onChange={setPlatforms} />

        {/* Period (only shown in keyword mode) */}
        {inputMode === "keyword" && (
          <div className="flex items-center gap-3">
            <label className="text-xs text-gray-500">周期：</label>
            {["weekly", "monthly"].map((v) => (
              <button
                key={v}
                onClick={() => setPeriod(v)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                  period === v
                    ? "bg-brand-50 text-brand-700 border-brand-200"
                    : "bg-white text-gray-500 border-gray-200 hover:border-gray-300"
                }`}
              >
                {v === "weekly" ? "每周" : "每月"}
              </button>
            ))}
            <RunButton onClick={handleRun} loading={isPending} className="ml-auto" />
          </div>
        )}

        {/* Run button for date range mode */}
        {inputMode === "date_range" && (
          <div className="flex justify-end">
            <RunButton onClick={handleRun} loading={isPending} />
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card text-center">
              <p className="text-3xl font-bold text-gray-900">{result.total_items}</p>
              <p className="text-gray-400 text-xs mt-1">采集条目</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-gray-900">{result.top_topics?.length}</p>
              <p className="text-gray-400 text-xs mt-1">热门话题</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-brand-600">{result.period_label}</p>
              <p className="text-gray-400 text-xs mt-1">报告周期</p>
            </div>
          </div>

          {/* Trend phase chart */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">趋势生命周期分布</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={phaseData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 12 }} />
                <YAxis tick={{ fill: "#9ca3af", fontSize: 12 }} />
                <Tooltip {...TOOLTIP_STYLE} />
                <Bar dataKey="count" fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top topics */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">TOP 话题关键词</h3>
            <div className="flex flex-wrap gap-2">
              {result.top_topics?.map((t: string, i: number) => (
                <span
                  key={t}
                  className="px-3 py-1 rounded-full text-sm font-medium"
                  style={{
                    background: `rgba(168,85,247,${0.07 + (1 - i / 20) * 0.12})`,
                    color: `rgba(109,40,217,${0.7 + (1 - i / 20) * 0.3})`,
                    fontSize: `${14 - i * 0.3}px`,
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* Top items */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">爆发力 TOP 10</h3>
            <div className="space-y-3">
              {topItems.map((item: any, i: number) => (
                <div key={i} className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-0">
                  <span className="text-gray-300 text-xs font-mono w-5 shrink-0 mt-0.5">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 truncate">{item.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <PlatformBadge platform={item.platform} />
                      <span className={`badge ${PHASE_COLORS[item.lifecycle] || PHASE_COLORS.unknown}`}>
                        {PHASE_LABELS[item.lifecycle] || item.lifecycle}
                      </span>
                      <span className="text-gray-400 text-xs">
                        病毒值 {item.virality_score?.toFixed(1)}
                      </span>
                    </div>
                  </div>
                  {item.url && (
                    <a href={item.url} target="_blank" rel="noreferrer"
                      className="text-brand-600 text-xs hover:underline shrink-0">
                      查看
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Content generation */}
          <ContentGeneratorPanel reportId={result.report_id} />

          {/* AI Narrative */}
          {result.narrative?.executive_summary && (
            <div className="card border-brand-200 bg-brand-50/30">
              <div className="flex items-center gap-2 mb-3">
                <span>🤖</span>
                <h3 className="text-sm font-semibold text-brand-700">AI 趋势解读</h3>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed">{result.narrative.executive_summary}</p>
              {result.narrative.deep_insights?.length > 0 && (
                <div className="mt-4 space-y-3">
                  {result.narrative.deep_insights.map((insight: any, i: number) => (
                    <div key={i} className="bg-white rounded-xl p-4 border border-brand-100">
                      <p className="text-gray-900 text-xs font-semibold mb-1">{insight.title}</p>
                      <p className="text-gray-500 text-xs leading-relaxed">{insight.body}</p>
                      {insight.implication && (
                        <p className="text-brand-600 text-xs mt-2">💡 {insight.implication}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
