"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface DecisionSummary {
  id: string;
  title: string;
  description: string;
  status: "active" | "closed";
  questionCount: number;
  voteCount: number;
  voters: string[];
  team: string[];
}

export default function DecisionPicker() {
  const [decisions, setDecisions] = useState<DecisionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/decisions")
      .then((res) => res.json())
      .then((data) => setDecisions(data.decisions ?? []))
      .catch(() => setDecisions([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-[#1a1a2e]">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-zinc-400 text-xs mb-3 font-mono">
            <span className="text-indigo-400">$</span>
            <span>company</span>
            <span className="text-zinc-600">/</span>
            <span>decide</span>
          </div>
          <h1 className="text-xl font-semibold text-zinc-100">
            Team Decisions
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Vote on active decisions. Click a card to cast your vote.
          </p>
        </div>

        {loading ? (
          <div className="text-center py-12 text-zinc-500 text-sm">
            Loading decisions...
          </div>
        ) : decisions.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-zinc-500 text-sm">
              No decisions found. Add YAML files to the decisions/ folder.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {decisions.map((d) => (
              <Link
                key={d.id}
                href={d.status === "closed" ? `/results/${d.id}` : `/vote/${d.id}`}
                className="block group"
              >
                <div
                  className={`rounded-xl border p-5 transition-all duration-200 ${
                    d.status === "closed"
                      ? "border-zinc-800/50 bg-[#16213e]/20 opacity-60 hover:opacity-80"
                      : "border-zinc-800/80 bg-[#16213e]/40 hover:border-indigo-500/30 hover:shadow-[0_0_20px_rgba(99,102,241,0.08)]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1.5">
                        <h2 className="text-base font-semibold text-zinc-100 truncate">
                          {d.title}
                        </h2>
                        {d.status === "closed" && (
                          <span className="inline-flex items-center rounded-full bg-zinc-800 px-2 py-0.5 text-[10px] font-medium text-zinc-500 ring-1 ring-inset ring-zinc-700/50 shrink-0">
                            Closed
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-zinc-400 leading-relaxed line-clamp-2">
                        {d.description}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span className="text-xs text-zinc-400">
                        {d.questionCount} question{d.questionCount !== 1 ? "s" : ""}
                      </span>
                      <span
                        className={`text-xs font-medium ${
                          d.voteCount === d.team.length
                            ? "text-emerald-400"
                            : d.voteCount > 0
                              ? "text-amber-400"
                              : "text-zinc-600"
                        }`}
                      >
                        {d.voteCount}/{d.team.length} voted
                      </span>
                    </div>
                  </div>

                  {/* Voter chips */}
                  {d.voters.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {d.team.map((name) => {
                        const hasVoted = d.voters.includes(name);
                        return (
                          <span
                            key={name}
                            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-medium ${
                              hasVoted
                                ? "bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20"
                                : "bg-zinc-800/50 text-zinc-600 ring-1 ring-inset ring-zinc-700/30"
                            }`}
                          >
                            <span
                              className={`h-1 w-1 rounded-full ${
                                hasVoted ? "bg-emerald-400" : "bg-zinc-600"
                              }`}
                            />
                            {name}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Footer links */}
        <div className="mt-8 flex items-center justify-center gap-4">
          <Link
            href="/results"
            className="text-xs text-zinc-400 hover:text-indigo-400 transition-colors"
          >
            View all results →
          </Link>
          <Link
            href="/admin"
            className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            Admin
          </Link>
        </div>
      </div>
    </div>
  );
}
