import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { formatDate, MODULE_META } from "../lib/utils";
import type { ReportSummary } from "../lib/api";

export default function ReportCard({ report }: { report: ReportSummary }) {
  const meta = MODULE_META[report.module] || { label: report.module, icon: "📄", color: "text-gray-500" };
  return (
    <Link
      to={`/reports/${report.id}`}
      className="card flex items-start gap-4 hover:border-gray-300 hover:shadow-md transition-all group"
    >
      <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-xl shrink-0">
        {meta.icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-semibold ${meta.color}`}>{meta.label}</span>
          {report.period_label && (
            <span className="text-gray-400 text-xs">{report.period_label}</span>
          )}
        </div>
        <p className="text-sm font-medium text-gray-900 truncate">{report.title}</p>
        <div className="flex items-center gap-3 mt-1.5">
          <span className="text-gray-400 text-xs">{report.total_items} 条数据</span>
          <span className="text-gray-400 text-xs">{formatDate(report.created_at)}</span>
        </div>
        {report.top_topics?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {report.top_topics.slice(0, 4).map((t) => (
              <span key={t} className="text-xs bg-slate-100 text-gray-500 px-2 py-0.5 rounded-full">
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
      <ChevronRight size={16} className="text-gray-300 group-hover:text-gray-500 transition-colors shrink-0 mt-1" />
    </Link>
  );
}
