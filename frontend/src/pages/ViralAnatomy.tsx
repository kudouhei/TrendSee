import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { runViralAnatomy } from "../lib/api";
import { PLATFORM_LABELS, formatNum } from "../lib/utils";
import RunButton from "../components/RunButton";
import PlatformBadge from "../components/PlatformBadge";

const ALL_PLATFORMS = ["xhs", "douyin"];

export default function ViralAnatomy() {
  const [topic, setTopic] = useState("");
  const [platforms, setPlatforms] = useState<string[]>(ALL_PLATFORMS);
  const [result, setResult] = useState<any>(null);

  const { mutate, isPending } = useMutation({
    mutationFn: runViralAnatomy,
    onSuccess: setResult,
  });

  const togglePlatform = (p: string) =>
    setPlatforms((prev) => prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">🔬 爆款解剖室</h1>
        <p className="text-gray-500 text-sm mt-1">反向拆解爆款内容，提炼可复用公式</p>
      </div>

      <div className="card space-y-4">
        <div>
          <label className="text-xs text-gray-500 mb-1.5 block">解剖话题</label>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900
                       focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            placeholder="例如：减肥、副业、考研..."
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {ALL_PLATFORMS.map((p) => (
            <button
              key={p}
              onClick={() => togglePlatform(p)}
              className={`badge border cursor-pointer transition-all ${
                platforms.includes(p)
                  ? "bg-brand-50 text-brand-700 border-brand-200"
                  : "bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300"
              }`}
            >
              {PLATFORM_LABELS[p]}
            </button>
          ))}
        </div>
        <RunButton onClick={() => mutate({ topic, platforms, limit_per_source: 20 })} loading={isPending} />
      </div>

      {result && (
        <div className="space-y-6">
          {/* Viral items */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">爆款 TOP 榜</h3>
            <div className="space-y-4">
              {result.viral_items?.map((item: any, i: number) => (
                <div key={i} className="bg-slate-50 rounded-xl p-4 border border-gray-100">
                  <div className="flex items-start gap-3">
                    <span className="text-rose-500 font-bold text-sm shrink-0">#{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-900 text-sm font-medium">{item.title}</p>
                      <div className="flex items-center gap-3 mt-2">
                        <PlatformBadge platform={item.platform} />
                        <span className="text-gray-500 text-xs">👍 {formatNum(item.likes)}</span>
                        <span className="text-gray-500 text-xs">💬 {formatNum(item.comments)}</span>
                        <span className="text-gray-500 text-xs">⭐ {formatNum(item.collects)}</span>
                      </div>
                      <div className="mt-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-gray-400">病毒传播指数</span>
                          <span className="text-xs text-rose-600 font-semibold">{item.virality_score?.toFixed(1)}</span>
                        </div>
                        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-rose-500 to-red-400 rounded-full"
                            style={{ width: `${Math.min(item.virality_score, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Title patterns */}
          {result.title_patterns?.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">爆款标题模式</h3>
              <div className="grid grid-cols-2 gap-3">
                {result.title_patterns.map((p: any) => (
                  <div key={p.pattern} className="bg-slate-50 rounded-xl p-3 border border-gray-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-rose-600 text-xs font-semibold">{p.pattern}</span>
                      <span className="text-gray-400 text-xs">{p.count} 个</span>
                    </div>
                    {p.examples.map((ex: string, i: number) => (
                      <p key={i} className="text-gray-500 text-xs truncate mt-1">· {ex}</p>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI anatomy */}
          {result.anatomy && (
            <div className="card border-rose-200 bg-rose-50/30">
              <div className="flex items-center gap-2 mb-4">
                <span>🤖</span>
                <h3 className="text-sm font-semibold text-rose-700">AI 爆款解剖报告</h3>
              </div>

              {result.anatomy.content_formula && (
                <div className="bg-white border border-rose-200 rounded-xl p-4 mb-4">
                  <p className="text-rose-600 text-xs font-semibold mb-1">🧬 爆款公式</p>
                  <p className="text-gray-900 text-sm font-medium">{result.anatomy.content_formula}</p>
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {result.anatomy.emotion_triggers?.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400 mb-2">情绪触发点</p>
                    {result.anatomy.emotion_triggers.map((e: string, i: number) => (
                      <div key={i} className="flex items-center gap-2 py-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-400 shrink-0" />
                        <p className="text-gray-600 text-xs">{e}</p>
                      </div>
                    ))}
                  </div>
                )}

                {result.anatomy.replication_tips?.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400 mb-2">复制技巧</p>
                    {result.anatomy.replication_tips.map((t: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 py-1.5">
                        <span className="text-rose-500 text-xs font-bold shrink-0">{i + 1}.</span>
                        <p className="text-gray-600 text-xs">{t}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {result.anatomy.title_formula && (
                <div className="mt-4 bg-white rounded-xl p-3 border border-rose-100">
                  <p className="text-xs text-gray-400 mb-1">标题公式</p>
                  <p className="text-gray-900 text-sm">{result.anatomy.title_formula}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
