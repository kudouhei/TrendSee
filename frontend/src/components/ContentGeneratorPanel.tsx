/**
 * ContentGeneratorPanel
 * Universal inline panel for generating and viewing XHS + WeChat content
 * from any module report. Drop it anywhere you have a report_id.
 */
import { useState } from "react";
import { generateContent, getReportContent, GeneratedContent } from "../lib/api";

interface Props {
  reportId: number | null | undefined;
}

const PLATFORMS = [
  { id: "xhs",    label: "📕 小红书图文" },
  { id: "wechat", label: "📰 公众号长文" },
] as const;

export default function ContentGeneratorPanel({ reportId }: Props) {
  const [selected, setSelected] = useState<string[]>(["xhs", "wechat"]);
  const [generating, setGenerating] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [contents, setContents] = useState<GeneratedContent[]>([]);
  const [activeTab, setActiveTab] = useState<string>("");

  const toggle = (id: string) =>
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);

  const handleGenerate = async () => {
    if (!reportId || selected.length === 0) return;
    setGenerating(true);
    setStatus("idle");
    try {
      await generateContent(reportId, selected);
      const data = await getReportContent(reportId);
      setContents(data);
      setStatus("success");
      if (data.length > 0) setActiveTab(data[0].output_platform);
    } catch {
      setStatus("error");
    } finally {
      setGenerating(false);
    }
  };

  const activeContent = contents.find((c) => c.output_platform === activeTab);

  return (
    <div className="card border-brand-200 bg-gradient-to-br from-brand-50/40 to-white space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className="text-base">✍️</span>
        <h3 className="text-sm font-semibold text-brand-700">一键生成图文内容</h3>
      </div>

      {/* Platform selector + button */}
      <div className="flex flex-wrap items-center gap-2">
        {PLATFORMS.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => toggle(id)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
              selected.includes(id)
                ? "bg-brand-50 text-brand-700 border-brand-300 font-medium"
                : "bg-white text-gray-400 border-gray-200 hover:border-gray-300"
            }`}
          >
            {label}
          </button>
        ))}

        <button
          onClick={handleGenerate}
          disabled={generating || !reportId || selected.length === 0}
          className="ml-auto text-xs px-4 py-1.5 rounded-lg bg-brand-600 text-white font-medium
                     hover:bg-brand-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center gap-1.5"
        >
          {generating && (
            <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          )}
          {generating ? "生成中…" : "立即生成"}
        </button>
      </div>

      {/* Status messages */}
      {status === "error" && (
        <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          ✗ 生成失败，请检查 AI API Key 配置后重试
        </p>
      )}

      {/* Generated content display */}
      {contents.length > 0 && (
        <div className="space-y-3 pt-1">
          {/* Tab row */}
          <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit border border-gray-200">
            {contents.map((c) => (
              <button
                key={c.output_platform}
                onClick={() => setActiveTab(c.output_platform)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === c.output_platform
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {c.output_platform === "xhs" ? "📕 小红书" : "📰 公众号"}
              </button>
            ))}
          </div>

          {/* Active content */}
          {activeContent && (
            <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <h4 className="text-gray-900 text-sm font-semibold leading-snug flex-1">
                  {activeContent.title}
                </h4>
                <button
                  onClick={() => navigator.clipboard.writeText(
                    `${activeContent.title}\n\n${activeContent.body}`
                  )}
                  className="shrink-0 text-xs text-gray-400 hover:text-brand-600 transition-colors border
                             border-gray-200 rounded-lg px-2 py-1 hover:border-brand-300"
                  title="复制全文"
                >
                  复制
                </button>
              </div>

              <p className="text-gray-600 text-xs leading-relaxed line-clamp-10 whitespace-pre-wrap">
                {activeContent.body}
              </p>

              {activeContent.hashtags?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-2 border-t border-gray-100">
                  {activeContent.hashtags.slice(0, 8).map((t) => (
                    <span key={t} className="text-brand-600 text-xs bg-brand-50 px-2 py-0.5 rounded-full">
                      #{t}
                    </span>
                  ))}
                </div>
              )}

              {activeContent.output_platform === "xhs" && activeContent.cover_prompt && (
                <div className="bg-slate-50 rounded-lg p-3 border border-gray-100">
                  <p className="text-gray-400 text-xs mb-1">🖼️ 封面图提示词（可用于 AI 生图）</p>
                  <p className="text-gray-600 text-xs italic">{activeContent.cover_prompt}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
