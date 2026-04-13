import { useState } from "react";
import { api } from "../lib/api";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle, Loader2 } from "lucide-react";

type Provider = "openai" | "deepseek";

const PROVIDER_META: Record<Provider, { label: string; color: string; models: string[]; docsUrl: string }> = {
  openai: {
    label: "OpenAI",
    color: "text-green-600",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    docsUrl: "https://platform.openai.com/api-keys",
  },
  deepseek: {
    label: "DeepSeek",
    color: "text-blue-600",
    models: ["deepseek-chat", "deepseek-reasoner"],
    docsUrl: "https://platform.deepseek.com",
  },
};

const MODEL_DESC: Record<string, string> = {
  "gpt-4o":             "最强综合能力，内容生成首选",
  "gpt-4o-mini":        "快速低价，适合高频分析",
  "gpt-4-turbo":        "长上下文，适合深度报告",
  "deepseek-chat":      "DeepSeek-V3，性价比极高，效果媲美 GPT-4o",
  "deepseek-reasoner":  "DeepSeek-R1，深度推理，适合垂直精分报告",
};

export default function Settings() {
  const [activeProvider, setActiveProvider] = useState<Provider>("openai");

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.get("/health").then((r) => r.data),
    refetchInterval: 15000,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">⚙️ 设置</h1>
        <p className="text-gray-500 text-sm mt-1">配置 AI 提供商、API 密钥和定时任务</p>
      </div>

      {/* System status */}
      <div className="card flex items-center gap-4">
        {health ? (
          <CheckCircle size={18} className="text-green-500 shrink-0" />
        ) : (
          <Loader2 size={18} className="text-gray-400 animate-spin shrink-0" />
        )}
        <div>
          <p className="text-gray-900 text-sm font-medium">
            后端服务 {health ? "运行正常" : "连接中..."}
          </p>
          <p className="text-gray-400 text-xs">http://localhost:8000</p>
        </div>
        {health && (
          <span className="ml-auto badge bg-green-50 text-green-700 border border-green-200">
            v{health.version}
          </span>
        )}
      </div>

      {/* AI Provider selector */}
      <div className="card space-y-5">
        <h3 className="text-sm font-semibold text-gray-900">AI 提供商</h3>

        <div className="grid grid-cols-2 gap-3">
          {(["openai", "deepseek"] as Provider[]).map((p) => {
            const meta = PROVIDER_META[p];
            return (
              <button
                key={p}
                onClick={() => setActiveProvider(p)}
                className={`rounded-xl border p-4 text-left transition-all ${
                  activeProvider === p
                    ? "border-brand-300 bg-brand-50 shadow-sm"
                    : "border-gray-200 bg-white hover:border-gray-300"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-sm font-semibold ${meta.color}`}>{meta.label}</span>
                  {activeProvider === p && (
                    <span className="badge bg-brand-50 text-brand-700 border border-brand-200 text-xs">
                      当前选择
                    </span>
                  )}
                </div>
                <p className="text-gray-500 text-xs">
                  {p === "openai" ? "GPT-4o / GPT-4o-mini" : "DeepSeek-V3 / R1"}
                </p>
                <p className="text-gray-400 text-xs mt-1">
                  {p === "openai" ? "业界标准，稳定可靠" : "低价高效，中文优化"}
                </p>
              </button>
            );
          })}
        </div>

        {/* Provider config */}
        <div className="bg-slate-50 rounded-xl p-4 space-y-4 border border-gray-100">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-semibold ${PROVIDER_META[activeProvider].color}`}>
              {PROVIDER_META[activeProvider].label} 配置
            </span>
            <a
              href={PROVIDER_META[activeProvider].docsUrl}
              target="_blank"
              rel="noreferrer"
              className="text-gray-400 hover:text-brand-600 text-xs ml-auto transition-colors"
            >
              获取 API Key →
            </a>
          </div>

          {activeProvider === "openai" ? (
            <ConfigRow envKey="OPENAI_API_KEY" desc="OpenAI 平台密钥，用于所有分析与内容生成" required />
          ) : (
            <ConfigRow envKey="DEEPSEEK_API_KEY" desc="DeepSeek 平台密钥，兼容 OpenAI SDK 接口" required />
          )}

          <div>
            <p className="text-xs text-gray-400 mb-2">可选模型</p>
            <div className="space-y-2">
              {PROVIDER_META[activeProvider].models.map((m) => (
                <div key={m} className="flex items-start gap-3 py-1.5 border-b border-gray-200 last:border-0">
                  <code className="text-brand-600 text-xs font-mono w-44 shrink-0">{m}</code>
                  <p className="text-gray-500 text-xs">{MODEL_DESC[m]}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* .env code snippet */}
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-200">
          <p className="text-gray-400 text-xs mb-2">在 <code className="text-brand-400">.env</code> 中设置：</p>
          <pre className="text-xs text-green-400 leading-relaxed">
{activeProvider === "openai"
  ? `AI_PROVIDER=openai\nOPENAI_API_KEY=sk-...\nOPENAI_MODEL=gpt-4o`
  : `AI_PROVIDER=deepseek\nDEEPSEEK_API_KEY=sk-...\nDEEPSEEK_MODEL=deepseek-chat`}
          </pre>
        </div>

        <p className="text-gray-400 text-xs">
          💡 两个密钥均填写时，系统将使用 <code className="text-brand-600 bg-brand-50 px-1 rounded">AI_PROVIDER</code> 指定的提供商，另一个作为自动备用。
        </p>
      </div>

      {/* Other keys */}
      <div className="card space-y-4">
        <h3 className="text-sm font-semibold text-gray-900">其他 API 密钥</h3>
        {[
          { key: "REDDIT_CLIENT_ID",     desc: "Reddit 数据采集（PRAW 官方 API）", required: false },
          { key: "REDDIT_CLIENT_SECRET", desc: "Reddit 数据采集（PRAW 官方 API）", required: false },
        ].map(({ key, desc, required }) => (
          <ConfigRow key={key} envKey={key} desc={desc} required={required} />
        ))}
      </div>

      {/* Scheduled tasks */}
      <div className="card space-y-4">
        <h3 className="text-sm font-semibold text-gray-900">定时任务</h3>
        <div className="space-y-3">
          {[
            { name: "趋势雷达（周报）", schedule: "每周一 08:00" },
            { name: "抖音热榜采集",     schedule: "每天 09:00" },
            { name: "Reddit 趋势",      schedule: "每 6 小时" },
            { name: "Google Trends",    schedule: "每天 07:00" },
          ].map(({ name, schedule }) => (
            <div key={name} className="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
              <div className="w-2 h-2 rounded-full bg-green-400 shrink-0" />
              <div className="flex-1">
                <p className="text-gray-900 text-sm">{name}</p>
                <p className="text-gray-400 text-xs">{schedule}</p>
              </div>
              <span className="badge bg-green-50 text-green-700 border border-green-200">运行中</span>
            </div>
          ))}
        </div>
        <p className="text-gray-400 text-xs">
          注：定时任务需要 Celery Beat 服务运行。详见 <code className="text-brand-600 bg-brand-50 px-1 rounded">docker-compose up</code>
        </p>
      </div>

      {/* Data source */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">数据源说明</h3>
        <div className="space-y-3 text-xs text-gray-500">
          <p>• <span className="text-red-600 font-medium">小红书</span>：通过 Playwright 无头浏览器抓取，建议配置 Cookie 提升稳定性</p>
          <p>• <span className="text-gray-700 font-medium">抖音</span>：抓取公开热榜页面，建议配置 Cookie</p>
          <p>• <span className="text-orange-600 font-medium">Reddit</span>：优先使用 PRAW 官方 API，无 Key 时降级为公开 JSON API</p>
          <p>• <span className="text-blue-600 font-medium">Google Trends</span>：使用 pytrends 库，无需密钥，注意请求频率限制</p>
        </div>
      </div>
    </div>
  );
}

function ConfigRow({ envKey, desc, required }: { envKey: string; desc: string; required: boolean }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
      <div className="flex-1">
        <p className="text-gray-900 text-sm font-mono">{envKey}</p>
        <p className="text-gray-400 text-xs mt-0.5">{desc}</p>
      </div>
      <span className={`badge border text-xs ${
        required
          ? "bg-red-50 text-red-600 border-red-200"
          : "bg-gray-50 text-gray-400 border-gray-200"
      }`}>
        {required ? "必填" : "可选"}
      </span>
    </div>
  );
}
