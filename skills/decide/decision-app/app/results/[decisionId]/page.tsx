"use client";

import { useState, useEffect, useRef, use } from "react";
import Link from "next/link";
import type { VoteResponse } from "@/lib/kv";
import type { Decision } from "@/lib/decisions";
import { VoterDetailCard } from "@/components/voter-detail-card";

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
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function getConsensusInfo(
  topVotes: number,
  totalVotes: number
): { bg: string; text: string; label: string } {
  if (totalVotes === 0)
    return { bg: "bg-zinc-800", text: "text-zinc-500", label: "No votes" };
  if (topVotes >= Math.ceil(totalVotes * 0.75))
    return { bg: "bg-emerald-500/10", text: "text-emerald-400", label: "Consensus" };
  if (topVotes >= Math.ceil(totalVotes * 0.5))
    return { bg: "bg-amber-500/10", text: "text-amber-400", label: "Majority" };
  return { bg: "bg-rose-500/10", text: "text-rose-400", label: "Split" };
}

export default function DecisionResultsPage({
  params,
}: {
  params: Promise<{ decisionId: string }>;
}) {
  const { decisionId } = use(params);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [responses, setResponses] = useState<VoteResponse[]>([]);
  const [conclusion, setConclusion] = useState<string | null>(null);
  const [loadingConclusion, setLoadingConclusion] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([
      fetch(`/api/decisions/${decisionId}`).then((r) => r.json()),
      fetch(`/api/responses?decisionId=${decisionId}`).then((r) => r.json()),
    ])
      .then(([decData, resData]) => {
        setDecision(decData.decision ?? null);
        setResponses(resData.responses ?? []);
      })
      .catch(() => {
        setDecision(null);
        setResponses([]);
      })
      .finally(() => setLoading(false));
  }, [decisionId]);

  const handleGenerateConclusion = async () => {
    setLoadingConclusion(true);
    try {
      const regen = conclusion ? "?regenerate=true" : "";
      const res = await fetch(`/api/conclude/${decisionId}${regen}`);
      const data = await res.json();
      if (data.conclusion) {
        setConclusion(data.conclusion);
      } else {
        alert(data.error || "Failed to generate conclusion");
      }
    } catch {
      alert("Network error generating conclusion");
    } finally {
      setLoadingConclusion(false);
    }
  };

  const handleExportPdf = async () => {
    if (!reportRef.current) return;
    setExportingPdf(true);
    try {
      const html2pdf = (await import("html2pdf.js")).default;
      const filename = `${decision?.title || decisionId}-results.pdf`;
      await html2pdf()
        .set({
          margin: [10, 10, 10, 10],
          filename,
          image: { type: "jpeg", quality: 0.98 },
          html2canvas: { scale: 2, backgroundColor: "#1a1a2e", useCORS: true },
          jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        } as Record<string, unknown>)
        .from(reportRef.current)
        .save();
    } catch {
      alert("Failed to generate PDF");
    } finally {
      setExportingPdf(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#1a1a2e] flex items-center justify-center">
        <p className="text-zinc-500 text-sm">Loading results...</p>
      </div>
    );
  }

  if (!decision) {
    return (
      <div className="min-h-screen bg-[#1a1a2e] flex items-center justify-center">
        <div className="text-center">
          <p className="text-zinc-500 text-sm">Decision not found.</p>
          <Link
            href="/"
            className="mt-4 inline-block text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            ← Back to decisions
          </Link>
        </div>
      </div>
    );
  }

  const sortedResponses = [...responses].sort(
    (a, b) => new Date(a.submittedAt).getTime() - new Date(b.submittedAt).getTime()
  );
  const submittedNames = sortedResponses.map((r) => r.name);
  const pendingNames = decision.team.filter((n) => !submittedNames.includes(n));

  return (
    <div className="min-h-screen bg-[#1a1a2e]">
      <div ref={reportRef} className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
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
            <span>{decisionId}</span>
            <span className="text-zinc-600">/</span>
            <span>results</span>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-semibold text-zinc-100">
                  {decision.title}
                </h1>
                {decision.status === "closed" && (
                  <span className="inline-flex items-center rounded-full bg-zinc-800 px-2.5 py-0.5 text-[10px] font-medium text-zinc-500 ring-1 ring-inset ring-zinc-700/50">
                    Closed
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm text-zinc-400">
                {responses.length}/{decision.team.length} team members voted
              </p>
            </div>
            <div className="flex gap-2">
              {decision.status === "active" && (
                <Link
                  href={`/vote/${decisionId}`}
                  className="rounded-lg px-3 py-1.5 text-xs font-medium text-zinc-400 ring-1 ring-zinc-700/50 hover:bg-zinc-800 transition-colors"
                >
                  ← Vote
                </Link>
              )}
              {responses.length > 0 && (
                <>
                  <button
                    onClick={handleExportPdf}
                    disabled={exportingPdf}
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer ring-1 ${
                      exportingPdf
                        ? "bg-zinc-700 text-zinc-400 ring-zinc-700/50 cursor-wait"
                        : "bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/30 ring-indigo-500/30"
                    }`}
                  >
                    {exportingPdf ? "Generating..." : "Export PDF"}
                  </button>
                  <a
                    href={`/api/export?decisionId=${decisionId}&format=single`}
                    className="rounded-lg bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-300 hover:bg-zinc-700 transition-colors ring-1 ring-zinc-700/50"
                  >
                    Export .md
                  </a>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Voter status */}
        <div className="mb-6 flex flex-wrap gap-2">
          {sortedResponses.map((r) => (
            <span
              key={r.name}
              className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400 ring-1 ring-inset ring-emerald-500/20"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              {r.name}
              <span className="text-emerald-400/50 text-[10px]">
                {timeAgo(r.submittedAt)}
              </span>
            </span>
          ))}
          {pendingNames.map((name) => (
            <span
              key={name}
              className="inline-flex items-center gap-1.5 rounded-full bg-zinc-800 px-3 py-1 text-xs font-medium text-zinc-500 ring-1 ring-inset ring-zinc-700/50"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
              {name}
            </span>
          ))}
        </div>

        {responses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-zinc-500 text-sm">No votes submitted yet.</p>
            {decision.status === "active" && (
              <Link
                href={`/vote/${decisionId}`}
                className="mt-4 inline-block text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                Be the first to vote →
              </Link>
            )}
          </div>
        ) : (
          <>
            {/* Vote matrix per question */}
            <div className="space-y-6 mb-8">
              {decision.questions.map((q) => {
                const tally: Record<string, string[]> = {};
                const reasonings: Record<string, { name: string; text: string }[]> = {};

                for (const r of responses) {
                  const answer = r.answers[q.id];
                  if (answer?.selected) {
                    if (!tally[answer.selected]) tally[answer.selected] = [];
                    tally[answer.selected].push(r.name);
                    if (answer.reasoning) {
                      if (!reasonings[answer.selected]) reasonings[answer.selected] = [];
                      reasonings[answer.selected].push({ name: r.name, text: answer.reasoning });
                    }
                  }
                }

                const sorted = Object.entries(tally).sort(
                  (a, b) => b[1].length - a[1].length
                );
                const topVotes = sorted[0]?.[1].length ?? 0;
                const consensus = getConsensusInfo(topVotes, responses.length);

                return (
                  <div
                    key={q.id}
                    className="rounded-xl border border-zinc-800/80 bg-[#16213e]/40 p-5"
                  >
                    {/* Question header */}
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div className="flex items-center gap-2.5">
                        <span className="inline-flex items-center rounded-md bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-300 ring-1 ring-inset ring-zinc-700/50 shrink-0">
                          {q.header}
                        </span>
                        <h3 className="text-sm font-medium text-zinc-100">
                          {q.question}
                        </h3>
                      </div>
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium shrink-0 ${consensus.bg} ${consensus.text}`}
                      >
                        {consensus.label}
                      </span>
                    </div>

                    {/* Vote distribution with names */}
                    <div className="space-y-3">
                      {sorted.map(([option, voters]) => {
                        const pct = Math.round((voters.length / responses.length) * 100);
                        const isWinner = option === sorted[0]?.[0];

                        return (
                          <div key={option} className="space-y-1.5">
                            <div className="flex items-center justify-between gap-3">
                              <span
                                className={`text-sm ${
                                  isWinner ? "text-zinc-100 font-medium" : "text-zinc-400"
                                }`}
                              >
                                {option}
                              </span>
                              <span className="text-xs text-zinc-400">
                                {voters.length}/{responses.length} ({pct}%)
                              </span>
                            </div>
                            <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${
                                  isWinner ? "bg-indigo-500" : "bg-zinc-600"
                                }`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            {/* Voter names */}
                            <div className="flex flex-wrap gap-1.5 mt-1">
                              {voters.map((name) => (
                                <span
                                  key={name}
                                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                                    isWinner
                                      ? "bg-indigo-500/10 text-indigo-400 ring-1 ring-inset ring-indigo-500/20"
                                      : "bg-zinc-800 text-zinc-500 ring-1 ring-inset ring-zinc-700/50"
                                  }`}
                                >
                                  {name}
                                </span>
                              ))}
                            </div>
                            {/* Reasoning */}
                            {reasonings[option]?.length > 0 && (
                              <div className="mt-2 pl-3 border-l-2 border-zinc-700/50 space-y-1.5">
                                {reasonings[option].map((r, i) => (
                                  <div key={i} className="text-xs">
                                    <span className="text-indigo-400 font-medium">
                                      {r.name}:
                                    </span>{" "}
                                    <span className="text-zinc-400">{r.text}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}

                      {/* Show who didn't answer */}
                      {(() => {
                        const voted = Object.values(tally).flat();
                        const skipped = submittedNames.filter((n) => !voted.includes(n));
                        if (skipped.length === 0) return null;
                        return (
                          <div className="pt-2 border-t border-zinc-800/50">
                            <span className="text-xs text-zinc-600">
                              Skipped: {skipped.join(", ")}
                            </span>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Per-Person Breakdown */}
            {sortedResponses.length > 0 && (
              <div className="mb-8">
                <button
                  onClick={() => setShowBreakdown(!showBreakdown)}
                  className="flex items-center gap-2 text-sm font-medium text-zinc-300 hover:text-zinc-100 transition-colors cursor-pointer mb-4"
                >
                  <span className="text-xs text-zinc-500">
                    {showBreakdown ? "▼" : "▶"}
                  </span>
                  Per-Person Breakdown
                  <span className="text-xs text-zinc-500">
                    ({sortedResponses.length} voter{sortedResponses.length !== 1 ? "s" : ""})
                  </span>
                </button>
                {showBreakdown && (
                  <div className="space-y-3">
                    {sortedResponses.map((r) => (
                      <VoterDetailCard
                        key={r.name}
                        name={r.name}
                        decision={decision}
                        response={r}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Council Synthesis Section */}
            <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-indigo-400 text-lg">🧠</span>
                  <h2 className="text-base font-semibold text-zinc-100">
                    Council Synthesis
                  </h2>
                </div>
                <button
                  onClick={handleGenerateConclusion}
                  disabled={loadingConclusion}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 cursor-pointer ${
                    loadingConclusion
                      ? "bg-zinc-700 text-zinc-400 cursor-wait"
                      : conclusion
                        ? "bg-zinc-700 text-zinc-300 hover:bg-zinc-600 ring-1 ring-inset ring-zinc-600"
                        : "bg-indigo-500 text-white hover:bg-indigo-400 shadow-[0_0_12px_rgba(99,102,241,0.3)]"
                  }`}
                >
                  {loadingConclusion ? "Analyzing..." : conclusion ? "Regenerate" : "Generate Conclusion"}
                </button>
              </div>

              {conclusion ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <div className="text-zinc-300 text-sm leading-relaxed whitespace-pre-wrap">
                    {conclusion.split(/^(##+ .+)$/gm).map((part, i) => {
                      if (part.startsWith("## ")) {
                        return (
                          <h3 key={i} className="text-zinc-100 font-semibold mt-4 mb-2 text-base">
                            {part.replace("## ", "")}
                          </h3>
                        );
                      }
                      if (part.startsWith("### ")) {
                        return (
                          <h4 key={i} className="text-zinc-200 font-medium mt-3 mb-1.5 text-sm">
                            {part.replace("### ", "")}
                          </h4>
                        );
                      }
                      return <span key={i}>{part.replace(/\*\*/g, "")}</span>;
                    })}
                  </div>
                </div>
              ) : (
                <p className="text-zinc-400 text-sm">
                  Click &quot;Generate Conclusion&quot; to get a Council synthesis of all votes
                  and reasoning. This uses Claude to analyze the team&apos;s inputs and provide
                  actionable recommendations.
                </p>
              )}
            </div>
          </>
        )}

        {/* Footer */}
        <div className="mt-6 mb-4 flex items-center justify-center gap-4">
          <Link
            href="/"
            className="text-xs text-zinc-400 hover:text-indigo-300 transition-colors"
          >
            ← All decisions
          </Link>
          <Link
            href="/results"
            className="text-xs text-zinc-400 hover:text-indigo-300 transition-colors"
          >
            All results →
          </Link>
        </div>
      </div>
    </div>
  );
}
