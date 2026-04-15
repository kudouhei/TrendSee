import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getReports, getReport, getReportContent, generateContent, regenerateNarrative } from "../lib/api";
import { MODULE_META, formatDate } from "../lib/utils";
import ReportCard from "../components/ReportCard";
import RunButton from "../components/RunButton";

const MODULES = ["all", "trend_radar", "comment_mining", "viral_anatomy", "vertical_deep"];

export default function Reports() {
  const queryClient = useQueryClient();
  const [activeModule, setActiveModule] = useState("all");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [generating, setGenerating] = useState(false);
  const [genStatus, setGenStatus] = useState<"idle" | "success" | "error">("idle");
  const [regenNarrative, setRegenNarrative] = useState(false);

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["reports", activeModule],
    queryFn: () => getReports(activeModule === "all" ? undefined : activeModule),
    refetchInterval: 10000,
  });

  const { data: detail } = useQuery({
    queryKey: ["report", selectedId],
    queryFn: () => getReport(selectedId!),
    enabled: !!selectedId,
  });

  const { data: contents = [] } = useQuery({
    queryKey: ["report-content", selectedId],
    queryFn: () => getReportContent(selectedId!),
    enabled: !!selectedId,
  });

  const handleRegenNarrative = async () => {
    if (!selectedId) return;
    setRegenNarrative(true);
    try {
      await regenerateNarrative(selectedId);
      await queryClient.invalidateQueries({ queryKey: ["report", selectedId] });
    } finally {
      setRegenNarrative(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedId) return;
    setGenerating(true);
    setGenStatus("idle");
    try {
      await generateContent(selectedId, ["xhs", "wechat"]);
      // Refresh the content list so the newly generated items appear immediately.
      await queryClient.invalidateQueries({ queryKey: ["report-content", selectedId] });
      setGenStatus("success");
    } catch {
      setGenStatus("error");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">📋 报告库</h1>
        <p className="text-gray-500 text-sm mt-1">所有模块的历史报告</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {MODULES.map((m) => {
          const meta = MODULE_META[m];
          return (
            <button
              key={m}
              onClick={() => setActiveModule(m)}
              className={`px-4 py-2 rounded-xl text-xs font-medium border transition-all ${
                activeModule === m
                  ? "bg-brand-50 text-brand-700 border-brand-200"
                  : "text-gray-500 border-gray-200 hover:border-gray-300 hover:text-gray-700 bg-white"
              }`}
            >
              {m === "all" ? "全部" : `${meta?.icon} ${meta?.label}`}
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* List */}
        <div className="space-y-3">
          {isLoading ? (
            <div className="text-gray-400 text-sm text-center py-8">加载中...</div>
          ) : reports.length === 0 ? (
            <div className="card text-center text-gray-400 text-sm py-12">暂无报告</div>
          ) : (
            reports.map((r) => (
              <div key={r.id} onClick={() => setSelectedId(r.id)} className="cursor-pointer">
                <div className={selectedId === r.id ? "ring-2 ring-brand-400 rounded-2xl" : ""}>
                  <ReportCard report={r} />
                </div>
              </div>
            ))
          )}
        </div>

        {/* Detail */}
        {detail && (
          <div className="space-y-4">
            <div className="card">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-xs text-gray-400 mb-1">{MODULE_META[detail.module]?.label || detail.module}</p>
                  <h2 className="text-gray-900 font-semibold">{detail.title}</h2>
                  <p className="text-gray-400 text-xs mt-1">{formatDate(detail.created_at)}</p>
                </div>
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <RunButton
                    label="生成内容"
                    onClick={handleGenerate}
                    loading={generating}
                  />
                  {genStatus === "success" && (
                    <span className="text-xs text-green-600 bg-green-50 border border-green-200 rounded-lg px-2 py-1">
                      ✓ 生成成功
                    </span>
                  )}
                  {genStatus === "error" && (
                    <span className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-2 py-1">
                      ✗ 生成失败，请重试
                    </span>
                  )}
                </div>
              </div>

              {detail.executive_summary ? (
                <div className="bg-slate-50 rounded-xl p-4 mb-4 border border-gray-100">
                  <p className="text-gray-400 text-xs mb-1">执行摘要</p>
                  <p className="text-gray-700 text-sm leading-relaxed">{detail.executive_summary}</p>
                </div>
              ) : (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4 flex items-start gap-3">
                  <span className="text-amber-500 text-sm mt-0.5">⚠️</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-amber-700 text-sm font-medium">AI 解读未生成</p>
                    <p className="text-amber-600 text-xs mt-0.5">可能是 AI API 超时或返回格式错误，点击重新生成。</p>
                  </div>
                  <button
                    onClick={handleRegenNarrative}
                    disabled={regenNarrative}
                    className="shrink-0 text-xs px-3 py-1.5 rounded-lg border border-amber-300 bg-white text-amber-700
                               hover:bg-amber-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {regenNarrative ? "生成中…" : "重新生成"}
                  </button>
                </div>
              )}

              {(detail.deep_insights as any[])?.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 mb-2">深度洞察</p>
                  <div className="space-y-2">
                    {(detail.deep_insights as any[]).map((insight, i) => (
                      <div key={i} className="bg-slate-50 rounded-xl p-3 border border-gray-100">
                        {typeof insight === "string" ? (
                          <p className="text-gray-600 text-xs">{insight}</p>
                        ) : (
                          <>
                            <p className="text-gray-900 text-xs font-semibold mb-1">{insight.title}</p>
                            <p className="text-gray-500 text-xs">{insight.body}</p>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Generated content */}
            {contents.length > 0 && (
              <div className="space-y-3">
                {contents.map((c) => (
                  <div key={c.id} className="card">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs font-semibold text-brand-600">
                        {c.output_platform === "xhs" ? "📕 小红书" : "📰 公众号"}
                      </span>
                    </div>
                    <h3 className="text-gray-900 text-sm font-medium mb-2">{c.title}</h3>
                    <p className="text-gray-500 text-xs leading-relaxed line-clamp-6">{c.body}</p>
                    {c.hashtags?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-3">
                        {c.hashtags.slice(0, 5).map((t) => (
                          <span key={t} className="text-brand-600 text-xs">#{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
