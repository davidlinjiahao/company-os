"use client";

interface OptionPillProps {
  label: string;
  description: string;
  selected: boolean;
  onClick: () => void;
}

export function OptionPill({
  label,
  description,
  selected,
  onClick,
}: OptionPillProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group relative w-full text-left rounded-lg border px-4 py-3 transition-all duration-200 cursor-pointer ${
        selected
          ? "border-indigo-500 bg-indigo-500/10 shadow-[0_0_12px_rgba(99,102,241,0.15)]"
          : "border-zinc-700/50 bg-zinc-800/30 hover:border-zinc-600 hover:bg-zinc-800/60"
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-all duration-200 ${
            selected
              ? "border-indigo-500 bg-indigo-500"
              : "border-zinc-600 group-hover:border-zinc-500"
          }`}
        >
          {selected && (
            <svg
              className="h-3 w-3 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={3}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 13l4 4L19 7"
              />
            </svg>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div
            className={`text-sm font-medium transition-colors ${
              selected ? "text-indigo-300" : "text-zinc-200"
            }`}
          >
            {label}
          </div>
          <div className="mt-0.5 text-xs text-zinc-300 leading-relaxed">
            {description}
          </div>
        </div>
      </div>
    </button>
  );
}
