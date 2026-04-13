import { PLATFORM_LABELS } from "../lib/utils";

const COLORS: Record<string, string> = {
  xhs:           "bg-red-50 text-red-600 border-red-200",
  douyin:        "bg-gray-100 text-gray-600 border-gray-200",
  reddit:        "bg-orange-50 text-orange-600 border-orange-200",
  google_trends: "bg-blue-50 text-blue-600 border-blue-200",
};

export default function PlatformBadge({ platform }: { platform: string }) {
  return (
    <span className={`badge border ${COLORS[platform] || "bg-gray-100 text-gray-500 border-gray-200"}`}>
      {PLATFORM_LABELS[platform] || platform}
    </span>
  );
}
