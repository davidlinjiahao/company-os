"use client";

import { useState } from "react";
import { DEFAULT_TEAM } from "@/lib/decisions";

interface NameSelectorProps {
  selected: string | null;
  onSelect: (name: string) => void;
  team?: string[];
}

export function NameSelector({ selected, onSelect, team }: NameSelectorProps) {
  const teamNames = team && team.length > 0 ? team : [];
  const merged = Array.from(new Set([...DEFAULT_TEAM, ...teamNames]));
  const names = merged;
  const [customName, setCustomName] = useState("");
  const isCustom = selected !== null && !names.includes(selected);

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {names.map((name) => (
          <button
            key={name}
            type="button"
            onClick={() => onSelect(name)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-all duration-200 cursor-pointer ${
              selected === name
                ? "bg-indigo-500 text-white shadow-[0_0_12px_rgba(99,102,241,0.3)]"
                : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-zinc-100 ring-1 ring-inset ring-zinc-700/50"
            }`}
          >
            {name}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={isCustom ? selected : customName}
          onChange={(e) => {
            setCustomName(e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && customName.trim()) {
              onSelect(customName.trim());
            }
          }}
          placeholder="Or type your name..."
          className="rounded-lg border border-zinc-700/50 bg-zinc-900/50 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-400 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 transition-colors w-48"
        />
        {customName.trim() && !isCustom && (
          <button
            type="button"
            onClick={() => onSelect(customName.trim())}
            className="rounded-lg bg-indigo-500 px-3 py-2 text-xs font-medium text-white hover:bg-indigo-400 transition-colors cursor-pointer"
          >
            Join
          </button>
        )}
      </div>
    </div>
  );
}
