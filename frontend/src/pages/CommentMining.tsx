import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { runCommentMining } from "../lib/api";
import { PLATFORM_LABELS } from "../lib/utils";
import RunButton from "../components/RunButton";
import ContentGeneratorPanel from "../components/ContentGeneratorPanel";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#16a34a",
  neutral:  "#9ca3af",
  negative: "#dc2626",
};

const SENTIMENT_LABELS: Record<string, string> = {
  positive: "正面 😊", neutral: "中性 😐", negative: "负面 😟",
};

const ALL_PLATFORMS = ["xhs", "douyin", "reddit"];

const TOOLTIP_STYLE = {
  contentStyle: { background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" },
  labelStyle: { color: "#6b7280" },
  itemStyle: { color: "#111827" },
};

export default function CommentMining() {
  const [topic, setTopic] = useState("");
  const [platforms, setPlatforms] = useState<string[]>(ALL_PLATFORMS);
  const [result, setResult] = useState<any>(null);

  const { mutate, isPending } = useMutation({
    mutationFn: runCommentMining,
    onSuccess: setResult,
  });

  const togglePlatform = (p: string) =>
    setPlatforms((prev) => prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]);

  const sentimentData = result
    ? Object.entries(result.sentiment_distribution || {}).map(([k, v]) => ({
        name: SENTIMENT_LABELS[k] || k,
        value: v as number,
        color: SENTIMENT_COLORS[k],
      }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">⛏️ 评论区挖矿</h1>
        <p className="text-gray-500 text-sm mt-1">深挖受众真实情绪，发现内容机会</p>
      </div>

      {/* Config */}
      <div className="card space-y-4">
        <div>
          <label className="text-xs text-gray-500 mb-1.5 block">挖矿话题</label>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900
                       focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            placeholder="例如：年轻人躺平、新能源汽车、AI工具..."
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
        <RunButton onClick={() => mutate({ topic, platforms, limit_per_source: 30 })} loading={isPending} />
      </div>

      {result && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card text-center">
              <p className="text-3xl font-bold text-gray-900">{result.total_posts_analysed}</p>
              <p className="text-gray-400 text-xs mt-1">分析条目</p>
            </div>
            <div className="card text-center">
              <p className={`text-3xl font-bold ${
                result.avg_sentiment_score > 0.1 ? "text-green-600" :
                result.avg_sentiment_score < -0.1 ? "text-red-600" : "text-gray-500"
              }`}>
                {result.avg_sentiment_score > 0 ? "+" : ""}{result.avg_sentiment_score?.toFixed(2)}
              </p>
              <p className="text-gray-400 text-xs mt-1">平均情绪值</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-amber-600">{result.top_words?.[0]?.word || "-"}</p>
              <p className="text-gray-400 text-xs mt-1">最高频词汇</p>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">情绪分布</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={sentimentData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 12 }} />
                  <YAxis dataKey="name" type="category" tick={{ fill: "#6b7280", fontSize: 12 }} width={70} />
                  <Tooltip {...TOOLTIP_STYLE} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {sentimentData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Word cloud */}
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">高频词云</h3>
              <div className="flex flex-wrap gap-2">
                {result.top_words?.slice(0, 20).map((w: any, i: number) => (
                  <span
                    key={w.word}
                    className="px-2.5 py-1 rounded-full"
                    style={{
                      background: `rgba(168,85,247,${0.06 + (1 - i / 20) * 0.12})`,
                      color: `rgba(109,40,217,${0.5 + (1 - i / 20) * 0.5})`,
                      fontSize: `${11 + (1 - i / 20) * 5}px`,
                    }}
                  >
                    {w.word} <span className="opacity-50">{w.count}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Content generation */}
          <ContentGeneratorPanel reportId={result.report_id} />

          {/* AI insights */}
          {result.ai_insights && (
            <div className="card border-amber-200 bg-amber-50/30">
              <div className="flex items-center gap-2 mb-4">
                <span>🤖</span>
                <h3 className="text-sm font-semibold text-amber-700">AI 评论区洞察</h3>
              </div>
              <p className="text-gray-700 text-sm mb-4">{result.ai_insights.audience_attitude}</p>

              {result.ai_insights.content_opportunities?.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 mb-2">创作机会</p>
                  <div className="space-y-2">
                    {result.ai_insights.content_opportunities.map((opp: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 bg-white rounded-xl p-3 border border-amber-100">
                        <span className="text-amber-600 text-xs font-bold shrink-0 mt-0.5">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <p className="text-gray-600 text-xs leading-relaxed">{opp}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.ai_insights.recommended_angle && (
                <div className="mt-4 bg-white border border-amber-200 rounded-xl p-4">
                  <p className="text-amber-700 text-xs font-semibold mb-1">💡 最推荐创作角度</p>
                  <p className="text-gray-700 text-sm">{result.ai_insights.recommended_angle}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
