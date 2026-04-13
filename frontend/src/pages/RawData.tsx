import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getRawItems, getJobs, triggerCollect } from "../lib/api";
import { formatDate, formatNum, PLATFORM_LABELS } from "../lib/utils";
import PlatformBadge from "../components/PlatformBadge";
import RunButton from "../components/RunButton";

const PLATFORMS = ["", "xhs", "douyin", "reddit", "google_trends"];

export default function RawData() {
  const [platform, setPlatform] = useState("");
  const [collectPlatform, setCollectPlatform] = useState("douyin");
  const [collectKeyword, setCollectKeyword] = useState("");

  const { data: items = [], refetch: refetchItems } = useQuery({
    queryKey: ["raw-items", platform],
    queryFn: () => getRawItems(platform || undefined),
    refetchInterval: 30000,
  });

  const { data: jobs = [], refetch: refetchJobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: getJobs,
    refetchInterval: 5000,
  });

  const { mutate: collect, isPending } = useMutation({
    mutationFn: () => triggerCollect(collectPlatform, collectKeyword),
    onSuccess: () => setTimeout(() => { refetchItems(); refetchJobs(); }, 2000),
  });

  const statusStyle: Record<string, string> = {
    success: "bg-green-50 text-green-700 border-green-200",
    running: "bg-amber-50 text-amber-700 border-amber-200",
    failed:  "bg-red-50 text-red-700 border-red-200",
    pending: "bg-gray-100 text-gray-500 border-gray-200",
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">🗄️ 原始数据</h1>
        <p className="text-gray-500 text-sm mt-1">查看采集的原始条目和任务历史</p>
      </div>

      {/* Quick collect */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">快速采集</h3>
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={collectPlatform}
            onChange={(e) => setCollectPlatform(e.target.value)}
            className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900
                       focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          >
            {PLATFORMS.slice(1).map((p) => (
              <option key={p} value={p}>{PLATFORM_LABELS[p]}</option>
            ))}
          </select>
          <input
            value={collectKeyword}
            onChange={(e) => setCollectKeyword(e.target.value)}
            className="flex-1 min-w-40 bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900
                       focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            placeholder="关键词（可空）"
          />
          <RunButton onClick={() => collect()} loading={isPending} label="开始采集" />
        </div>
      </div>

      {/* Recent jobs */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">最近任务</h3>
        <div className="space-y-2">
          {jobs.slice(0, 8).map((job) => (
            <div key={job.id} className="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
              <span className={`badge border text-xs ${statusStyle[job.status] || statusStyle.pending}`}>
                {job.status}
              </span>
              <span className="text-gray-600 text-xs flex-1">{job.job_type}</span>
              <span className="text-gray-400 text-xs">
                {job.result_summary ? `保存 ${(job.result_summary as any).saved || 0} 条` : ""}
              </span>
              <span className="text-gray-300 text-xs shrink-0">
                {job.created_at ? formatDate(job.created_at) : ""}
              </span>
            </div>
          ))}
          {jobs.length === 0 && (
            <p className="text-gray-400 text-sm text-center py-4">暂无任务</p>
          )}
        </div>
      </div>

      {/* Items table */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <h3 className="text-sm font-semibold text-gray-900">原始条目</h3>
          <span className="text-gray-400 text-xs">共 {items.length} 条</span>
          <div className="ml-auto flex gap-2 flex-wrap">
            {PLATFORMS.map((p) => (
              <button
                key={p || "all"}
                onClick={() => setPlatform(p)}
                className={`badge border cursor-pointer transition-all ${
                  platform === p
                    ? "bg-brand-50 text-brand-700 border-brand-200"
                    : "bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300"
                }`}
              >
                {p ? PLATFORM_LABELS[p] : "全部"}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left text-gray-400 font-medium pb-3 pr-4">平台</th>
                <th className="text-left text-gray-400 font-medium pb-3 pr-4 w-1/2">标题</th>
                <th className="text-right text-gray-400 font-medium pb-3 pr-4">点赞</th>
                <th className="text-right text-gray-400 font-medium pb-3 pr-4">评论</th>
                <th className="text-right text-gray-400 font-medium pb-3">采集时间</th>
              </tr>
            </thead>
            <tbody>
              {items.slice(0, 50).map((item) => (
                <tr key={item.id} className="border-b border-gray-50 hover:bg-slate-50 transition-colors">
                  <td className="py-2.5 pr-4">
                    <PlatformBadge platform={item.platform} />
                  </td>
                  <td className="py-2.5 pr-4 max-w-xs">
                    <a href={item.url} target="_blank" rel="noreferrer"
                      className="text-gray-700 hover:text-brand-600 truncate block hover:underline">
                      {item.title}
                    </a>
                  </td>
                  <td className="py-2.5 pr-4 text-right text-gray-500">{formatNum(item.likes)}</td>
                  <td className="py-2.5 pr-4 text-right text-gray-500">{formatNum(item.comments)}</td>
                  <td className="py-2.5 text-right text-gray-400">{formatDate(item.collected_at)}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center text-gray-300 py-8">暂无数据</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
