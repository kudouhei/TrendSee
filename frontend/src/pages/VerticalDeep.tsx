import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { runVerticalDeep } from "../lib/api";
import { PLATFORM_LABELS, PHASE_LABELS, PHASE_COLORS } from "../lib/utils";
import RunButton from "../components/RunButton";
import PlatformGroupSelector from "../components/PlatformGroupSelector";

const ALL_PLATFORMS = ["xhs", "douyin", "reddit", "google_trends"];

export default function VerticalDeep() {
  const [vertical, setVertical] = useState("");
  const [subTopics, setSubTopics] = useState("");
  const [platforms, setPlatforms] = useState<string[]>(ALL_PLATFORMS);
  const [outputTypes, setOutputTypes] = useState<string[]>(["wechat", "video_script"]);
  const [result, setResult] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"report" | "wechat" | "video">("report");

  const { mutate, isPending } = useMutation({
    mutationFn: runVerticalDeep,
    onSuccess: (data) => { setResult(data); setActiveTab("report"); },
  });

  const handleRun = () => mutate({
    vertical,
    sub_topics: subTopics.split(",").map((s) => s.trim()).filter(Boolean),
    platforms,
    output_types: outputTypes,
    limit_per_source: 20,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">🎯 垂直精分</h1>
        <p className="text-gray-500 text-sm mt-1">深度行业报告 + 视频脚本，每月 1-2 期</p>
      </div>

      <div className="card space-y-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500 mb-1.5 block">垂直领域</label>
            <input
              value={vertical}
              onChange={(e) => setVertical(e.target.value)}
              className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900
                         focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              placeholder="例如：新能源汽车、国货美妆、AI工具..."
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1.5 block">子话题（逗号分隔）</label>
            <input
              value={subTopics}
              onChange={(e) => setSubTopics(e.target.value)}
              className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900
                         focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              placeholder="价格战, 用户体验, 出海战略..."
            />
          </div>
        </div>
        <PlatformGroupSelector selected={platforms} onChange={setPlatforms} />
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">输出格式：</span>
          {[
            { id: "wechat", label: "公众号长文" },
            { id: "video_script", label: "视频脚本" },
          ].map(({ id, label }) => (
            <button
              key={id}
              onClick={() =>
                setOutputTypes((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])
              }
              className={`badge border cursor-pointer transition-all ${
                outputTypes.includes(id)
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <RunButton onClick={handleRun} loading={isPending} />
      </div>

      {result && (
        <div className="space-y-6">
          {/* Tabs */}
          <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit border border-gray-200">
            {[
              { id: "report", label: "📊 深度报告" },
              ...(result.generated_content?.wechat ? [{ id: "wechat", label: "📰 公众号" }] : []),
              ...(result.generated_content?.video_script ? [{ id: "video", label: "🎬 视频脚本" }] : []),
            ].map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                  activeTab === id
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Report tab */}
          {activeTab === "report" && (
            <div className="space-y-4">
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">子话题数据概览</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  {Object.entries(result.sub_analysis || {}).map(([sub, data]: [string, any]) => (
                    <div key={sub} className="bg-slate-50 rounded-xl p-4 border border-gray-100">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-gray-900 text-sm font-medium">{sub}</p>
                        <span className={`badge ${PHASE_COLORS[data.phase] || PHASE_COLORS.unknown}`}>
                          {PHASE_LABELS[data.phase] || data.phase}
                        </span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div>
                          <p className="text-gray-400 text-xs">分析量</p>
                          <p className="text-gray-900 text-sm font-semibold">{data.total}</p>
                        </div>
                        <div>
                          <p className="text-gray-400 text-xs">平均病毒值</p>
                          <p className="text-emerald-600 text-sm font-semibold">{data.avg_virality?.toFixed(1)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {result.deep_report && (
                <div className="card border-emerald-200 bg-emerald-50/30">
                  <div className="flex items-center gap-2 mb-4">
                    <span>🤖</span>
                    <h3 className="text-sm font-semibold text-emerald-700">AI 深度报告</h3>
                    {result.deep_report.report_title && (
                      <span className="text-gray-400 text-xs ml-auto">{result.deep_report.report_title}</span>
                    )}
                  </div>
                  <p className="text-gray-700 text-sm leading-relaxed mb-4">{result.deep_report.industry_overview}</p>

                  {result.deep_report.key_findings?.length > 0 && (
                    <div className="space-y-2 mb-4">
                      <p className="text-xs text-gray-400">核心发现</p>
                      {result.deep_report.key_findings.map((f: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 bg-white rounded-xl p-3 border border-emerald-100">
                          <span className="text-emerald-600 text-xs font-bold shrink-0">{i + 1}.</span>
                          <p className="text-gray-600 text-xs leading-relaxed">{f}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {result.deep_report.content_opportunities?.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-400 mb-2">创作机会</p>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                        {result.deep_report.content_opportunities.map((opp: any, i: number) => (
                          <div key={i} className="bg-white rounded-xl p-3 border border-emerald-100">
                            <p className="text-emerald-700 text-xs font-semibold mb-1">{opp.angle}</p>
                            <p className="text-gray-500 text-xs">{opp.format} · {opp.why}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* WeChat tab */}
          {activeTab === "wechat" && result.generated_content?.wechat && (
            <div className="card">
              <div className="border-b border-gray-100 pb-4 mb-4">
                <h2 className="text-lg font-bold text-gray-900">{result.generated_content.wechat.title}</h2>
                {result.generated_content.wechat.subtitle && (
                  <p className="text-gray-500 text-sm mt-1">{result.generated_content.wechat.subtitle}</p>
                )}
              </div>
              <pre className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap font-sans">
                {result.generated_content.wechat.body}
              </pre>
              {result.generated_content.wechat.hashtags?.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100">
                  {result.generated_content.wechat.hashtags.map((t: string) => (
                    <span key={t} className="text-brand-600 text-xs">#{t}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Video script tab */}
          {activeTab === "video" && result.generated_content?.video_script && (
            <div className="space-y-4">
              <div className="card">
                <h2 className="text-lg font-bold text-gray-900 mb-2">{result.generated_content.video_script.video_title}</h2>
                {result.generated_content.video_script.hook && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                    <p className="text-amber-700 text-xs font-semibold mb-1">⚡ 开场钩子（前15秒）</p>
                    <p className="text-gray-700 text-sm">{result.generated_content.video_script.hook}</p>
                  </div>
                )}
              </div>

              {result.generated_content.video_script.outline?.map((section: any, i: number) => (
                <div key={i} className="card">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="bg-brand-50 text-brand-700 text-xs font-bold px-2 py-1 rounded-lg border border-brand-100">
                      {i + 1}
                    </span>
                    <h3 className="text-gray-900 text-sm font-semibold">{section.section}</h3>
                    <span className="text-gray-400 text-xs ml-auto">{section.duration}</span>
                  </div>
                  <div className="space-y-1 mb-3">
                    {section.key_points?.map((pt: string, j: number) => (
                      <p key={j} className="text-gray-500 text-xs">· {pt}</p>
                    ))}
                  </div>
                  {section.visual_note && (
                    <div className="bg-blue-50 rounded-lg p-2 border border-blue-100">
                      <p className="text-blue-600 text-xs">🎬 画面: {section.visual_note}</p>
                    </div>
                  )}
                </div>
              ))}

              {result.generated_content.video_script.call_to_action && (
                <div className="card bg-brand-50 border-brand-200">
                  <p className="text-brand-700 text-xs font-semibold mb-1">📢 结尾号召</p>
                  <p className="text-gray-700 text-sm">{result.generated_content.video_script.call_to_action}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
