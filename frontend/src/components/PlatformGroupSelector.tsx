import { cn } from "../lib/utils";

const GROUPS = [
  {
    label: "🇨🇳 国内平台",
    platforms: ["xhs", "douyin"],
    labels: { xhs: "小红书", douyin: "抖音" },
    activeClass: "bg-red-50 text-red-700 border-red-200",
  },
  {
    label: "🌐 海外平台",
    platforms: ["reddit", "google_trends"],
    labels: { reddit: "Reddit", google_trends: "Google趋势" },
    activeClass: "bg-blue-50 text-blue-700 border-blue-200",
  },
] as const;

type KnownPlatform = "xhs" | "douyin" | "reddit" | "google_trends";

interface Props {
  selected: string[];
  onChange: (platforms: string[]) => void;
  /** 限制只展示某些平台，默认全部 */
  available?: string[];
}

export default function PlatformGroupSelector({ selected, onChange, available }: Props) {
  const toggle = (p: string) =>
    onChange(
      selected.includes(p) ? selected.filter((x) => x !== p) : [...selected, p]
    );

  const toggleGroup = (platforms: readonly string[]) => {
    const visible = available ? platforms.filter((p) => available.includes(p)) : platforms;
    const allOn = visible.every((p) => selected.includes(p));
    if (allOn) {
      onChange(selected.filter((p) => !visible.includes(p)));
    } else {
      const toAdd = visible.filter((p) => !selected.includes(p));
      onChange([...selected, ...toAdd]);
    }
  };

  return (
    <div className="flex flex-wrap gap-4">
      {GROUPS.map((group) => {
        const visible = available
          ? group.platforms.filter((p) => available.includes(p))
          : group.platforms;
        if (visible.length === 0) return null;

        const allOn = visible.every((p) => selected.includes(p));

        return (
          <div key={group.label} className="flex items-center gap-2">
            {/* 分组标签（点击全选/全取消本组） */}
            <button
              onClick={() => toggleGroup(group.platforms)}
              className={cn(
                "text-xs px-2 py-1 rounded-lg border font-medium transition-all select-none",
                allOn
                  ? "bg-gray-100 text-gray-600 border-gray-300"
                  : "bg-white text-gray-400 border-gray-200 hover:border-gray-300"
              )}
              title={allOn ? "取消全组" : "全选本组"}
            >
              {group.label}
            </button>

            <div className="w-px h-4 bg-gray-200" />

            {/* 各平台按钮 */}
            {visible.map((p) => (
              <button
                key={p}
                onClick={() => toggle(p)}
                className={cn(
                  "badge border cursor-pointer transition-all text-xs",
                  selected.includes(p)
                    ? group.activeClass
                    : "bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300"
                )}
              >
                {group.labels[p as KnownPlatform] ?? p}
              </button>
            ))}
          </div>
        );
      })}
    </div>
  );
}
