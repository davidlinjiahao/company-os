"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ResultsGrid } from "@/components/results-grid";
import type { VoteResponse } from "@/lib/kv";

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

interface DecisionFull {
  id: string;
  title: string;
  description: string;
  status: "active" | "closed";
  source?: string;
  team: string[];
  questions: {
    id: string;
    question: string;
    header: string;
    options: { label: string; description: string }[];
  }[];
}

export default function ResultsSummaryPage() {
  const [decisions, setDecisions] = useState<DecisionFull[]>([]);
  const [responses, setResponses] = useState<VoteResponse[]>([]);
  const [summaries, setSummaries] = useState<DecisionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/decisions").then((r) => r.json()),
      fetch("/api/responses").then((r) => r.json()),
    ])
      .then(async ([decData, resData]) => {
        const sums: DecisionSummary[] = decData.decisions ?? [];
        setSummaries(sums);
        setResponses(resData.responses ?? []);

        // Fetch full decision data for each
        const fullDecisions = await Promise.all(
          sums.map((s: DecisionSummary) =>
            fetch(`/api/decisions/${s.id}`)
              .then((r) => r.json())
              .then((d) => d.decision as DecisionFull)
          )
        );
        setDecisions(fullDecisions.filter(Boolean));
      })
      .catch(() => {
        setSummaries([]);
        setResponses([]);
      })
      .finally(() => setLoading(false));
  }, []);

  const totalVoters = new Set(responses.map((r) => r.name)).size;
  const allTeam = new Set(summaries.flatMap((s) => s.team));

  return (
    <div className="min-h-screen bg-[#1a1a2e]">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-zinc-400 text-xs mb-3 font-mono">
            <span className="text-indigo-400">$</span>
            <span>company</span>
            <span className="text-zinc-600">/</span>
            <Link href="/" className="hover:text-indigo-400 transition-colors">
              decide
            </Link>
            <span className="text-zinc-600">/</span>
            <span>results</span>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-zinc-100">
                All Results
              </h1>
              <p className="mt-1 text-sm text-zinc-400">
                {totalVoters}/{allTeam.size} unique voters across{" "}
                {summaries.length} decisions
              </p>
            </div>
            <div className="flex gap-2">
              <Link
                href="/"
                className="rounded-lg px-3 py-1.5 text-xs font-medium text-zinc-400 ring-1 ring-zinc-700/50 hover:bg-zinc-800 transition-colors"
              >
                ← Decisions
              </Link>
              {responses.length > 0 && (
                <a
                  href="/api/export"
                  className="rounded-lg bg-indigo-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-400 transition-colors shadow-[0_0_8px_rgba(99,102,241,0.2)]"
                >
                  Export All .md
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Per-decision links */}
        {summaries.length > 0 && (
          <div className="mb-6 flex flex-wrap gap-2">
            {summaries.map((s) => (
              <Link
                key={s.id}
                href={`/results/${s.id}`}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset transition-colors ${
                  s.status === "closed"
                    ? "bg-zinc-800/50 text-zinc-500 ring-zinc-700/30 hover:bg-zinc-800"
                    : "bg-indigo-500/10 text-indigo-400 ring-indigo-500/20 hover:bg-indigo-500/20"
                }`}
              >
                {s.title.replace("Decision: ", "")}
                <span className="text-[10px] opacity-60">
                  {s.voteCount}/{s.team.length}
                </span>
              </Link>
            ))}
          </div>
        )}

        {/* Results */}
        {loading ? (
          <div className="text-center py-12 text-zinc-500 text-sm">
            Loading results...
          </div>
        ) : responses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-zinc-500 text-sm">No votes submitted yet.</p>
            <Link
              href="/"
              className="mt-4 inline-block text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Start voting →
            </Link>
          </div>
        ) : (
          <ResultsGrid decisions={decisions} responses={responses} />
        )}
      </div>
    </div>
  );
}
