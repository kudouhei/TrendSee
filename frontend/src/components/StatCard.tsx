import { cn } from "../lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon?: React.ReactNode;
  className?: string;
}

export default function StatCard({ label, value, sub, icon, className }: StatCardProps) {
  return (
    <div className={cn("card flex items-start gap-4", className)}>
      {icon && (
        <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-xl shrink-0">
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {sub && <p className="text-gray-400 text-xs mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}
