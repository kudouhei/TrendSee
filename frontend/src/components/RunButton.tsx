import { Loader2, Play } from "lucide-react";
import { cn } from "../lib/utils";

interface RunButtonProps {
  onClick: () => void;
  loading?: boolean;
  label?: string;
  className?: string;
}

export default function RunButton({ onClick, loading, label = "立即运行", className }: RunButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={cn("btn-primary flex items-center gap-2", className)}
    >
      {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
      {loading ? "运行中..." : label}
    </button>
  );
}
