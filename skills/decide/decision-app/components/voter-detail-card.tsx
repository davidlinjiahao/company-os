"use client";

import type { Decision } from "@/lib/decisions";
import type { VoteResponse } from "@/lib/kv";

interface VoterDetailCardProps {
  name: string;
  decision: Decision;
  response: VoteResponse;
}

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;

  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;

  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function VoterDetailCard({
  name,
  decision,
  response,
}: VoterDetailCardProps) {
  return (
    <div className="rounded-lg border border-zinc-800/50 bg-[#16213e]/20 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="text-sm font-medium text-zinc-200">{name}</span>
        </div>
        <span className="text-xs text-zinc-400">
          {timeAgo(response.submittedAt)}
        </span>
      </div>
      <div className="space-y-2">
        {decision.questions.map((q) => {
          const answer = response.answers[q.id];
          if (!answer?.selected) return null;
          return (
            <div key={q.id} className="text-xs">
              <div className="flex items-start gap-2">
                <span className="inline-flex items-center rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] font-medium text-zinc-400 ring-1 ring-inset ring-zinc-700/50 shrink-0 mt-0.5">
                  {q.header}
                </span>
                <span className="text-indigo-400 font-medium">
                  {answer.selected}
                </span>
              </div>
              {answer.reasoning && (
                <p className="text-zinc-400 mt-1 ml-[calc(0.375rem+0.5rem)] leading-relaxed">
                  {answer.reasoning}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
