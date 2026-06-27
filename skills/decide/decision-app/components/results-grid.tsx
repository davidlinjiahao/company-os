"use client";

import type { Decision } from "@/lib/decisions";
import type { VoteResponse } from "@/lib/kv";
import { useState } from "react";

interface ResultsGridProps {
  decisions: Decision[];
  responses: VoteResponse[];
}

function getConsensusColor(
  topVotes: number,
  totalVotes: number
): { bg: string; text: string; label: string } {
  if (totalVotes === 0)
    return { bg: "bg-zinc-800", text: "text-zinc-500", label: "No votes" };
  if (topVotes >= Math.ceil(totalVotes * 0.75))
    return {
      bg: "bg-emerald-500/10",
      text: "text-emerald-400",
      label: "Consensus",
    };
  if (topVotes >= Math.ceil(totalVotes * 0.5))
    return {
      bg: "bg-amber-500/10",
      text: "text-amber-400",
      label: "Majority",
    };
  return { bg: "bg-rose-500/10", text: "text-rose-400", label: "Split" };
}

export function ResultsGrid({ decisions, responses }: ResultsGridProps) {
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);

  return (
    <div className="space-y-8">
      {decisions.map((decision) => {
        const decisionResponses = responses.filter(
          (r) => r.decisionId === decision.id
        );

        return (
          <section key={decision.id} className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-zinc-100">
                {decision.title}
              </h2>
              <p className="mt-0.5 text-xs text-zinc-500">
                {decision.description}
              </p>
            </div>
            <div className="space-y-3">
              {decision.questions.map((q) => {
                // Tally votes
                const tally: Record<string, string[]> = {};
                for (const r of decisionResponses) {
                  const answer = r.answers[q.id];
                  if (answer) {
                    if (!tally[answer.selected]) tally[answer.selected] = [];
                    tally[answer.selected].push(r.name);
                  }
                }
                const sorted = Object.entries(tally).sort(
                  (a, b) => b[1].length - a[1].length
                );
                const topVotes = sorted[0]?.[1].length ?? 0;
                const consensus = getConsensusColor(
                  topVotes,
                  decisionResponses.length
                );
                const isExpanded = expandedQuestion === q.id;

                return (
                  <div
                    key={q.id}
                    className="rounded-xl border border-zinc-800/80 bg-[#16213e]/40 overflow-hidden"
                  >
                    <button
                      type="button"
                      onClick={() =>
                        setExpandedQuestion(isExpanded ? null : q.id)
                      }
                      className="w-full p-4 text-left flex items-center justify-between gap-3 cursor-pointer hover:bg-zinc-800/20 transition-colors"
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span className="inline-flex items-center rounded-md bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-400 ring-1 ring-inset ring-zinc-700/50 shrink-0">
                          {q.header}
                        </span>
                        <span className="text-sm text-zinc-200 truncate">
                          {q.question}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${consensus.bg} ${consensus.text}`}
                        >
                          {consensus.label}
                        </span>
                        {sorted[0] && (
                          <span className="text-xs text-zinc-500">
                            {sorted[0][0]} ({sorted[0][1].length}/
                            {decisionResponses.length})
                          </span>
                        )}
                        <svg
                          className={`h-4 w-4 text-zinc-500 transition-transform duration-200 ${
                            isExpanded ? "rotate-180" : ""
                          }`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </div>
                    </button>
                    {isExpanded && (
                      <div className="border-t border-zinc-800/80 p-4 space-y-4">
                        {/* Vote distribution */}
                        <div className="space-y-2">
                          {sorted.map(([option, voters]) => {
                            const pct = Math.round(
                              (voters.length / decisionResponses.length) * 100
                            );
                            return (
                              <div key={option} className="space-y-1">
                                <div className="flex justify-between text-xs">
                                  <span className="text-zinc-300">
                                    {option}
                                  </span>
                                  <span className="text-zinc-500">
                                    {voters.join(", ")} ({pct}%)
                                  </span>
                                </div>
                                <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                                  <div
                                    className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                                    style={{ width: `${pct}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                        {/* Reasoning */}
                        {decisionResponses.some(
                          (r) => r.answers[q.id]?.reasoning
                        ) && (
                          <div className="space-y-2 border-t border-zinc-800/50 pt-3">
                            <h4 className="text-xs font-medium text-zinc-400">
                              Reasoning
                            </h4>
                            {decisionResponses
                              .filter((r) => r.answers[q.id]?.reasoning)
                              .map((r) => (
                                <div
                                  key={r.name}
                                  className="rounded-lg bg-zinc-900/50 px-3 py-2"
                                >
                                  <span className="text-xs font-medium text-indigo-400">
                                    {r.name}:
                                  </span>{" "}
                                  <span className="text-xs text-zinc-400">
                                    {r.answers[q.id].reasoning}
                                  </span>
                                </div>
                              ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
