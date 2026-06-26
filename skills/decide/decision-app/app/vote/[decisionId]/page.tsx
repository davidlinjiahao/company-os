"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { NameSelector } from "@/components/name-selector";
import { DecisionSection } from "@/components/decision-section";
import { MarkdownViewer } from "@/components/markdown-viewer";
import type { Decision } from "@/lib/decisions";

export default function VotePage({
  params,
}: {
  params: Promise<{ decisionId: string }>;
}) {
  const { decisionId } = use(params);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [selectedName, setSelectedName] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    try { return localStorage.getItem(`lastVoterName`); } catch { return null; }
  });
  const [answers, setAnswers] = useState<
    Record<string, { selected: string; reasoning: string }>
  >({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [loadingDecision, setLoadingDecision] = useState(true);
  const [loadingExisting, setLoadingExisting] = useState(false);

  const draftKey = `draft:${decisionId}:${selectedName ?? ""}`;

  // Restore draft from localStorage on name selection
  useEffect(() => {
    if (!selectedName || !decisionId) return;
    try {
      const saved = localStorage.getItem(`draft:${decisionId}:${selectedName}`);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === "object") {
          setAnswers(parsed);
        }
      }
    } catch { /* ignore corrupt data */ }
  }, [selectedName, decisionId]);

  // Auto-save draft to localStorage whenever answers change
  useEffect(() => {
    if (!selectedName || !decisionId || submitted) return;
    const hasContent = Object.values(answers).some(a => a.selected || a.reasoning);
    if (!hasContent) return;
    try {
      localStorage.setItem(draftKey, JSON.stringify(answers));
    } catch { /* storage full, ignore */ }
  }, [answers, draftKey, selectedName, decisionId, submitted]);

  // Load decision data
  useEffect(() => {
    fetch(`/api/decisions/${decisionId}`)
      .then((res) => res.json())
      .then((data) => setDecision(data.decision ?? null))
      .catch(() => setDecision(null))
      .finally(() => setLoadingDecision(false));
  }, [decisionId]);

  // Load existing responses when name is selected
  useEffect(() => {
    if (!selectedName || !decisionId) return;
    setLoadingExisting(true);
    fetch(`/api/responses?decisionId=${decisionId}&name=${selectedName}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.response) {
          setAnswers(data.response.answers);
          setSubmitted(true);
          // Clear draft since server has the submitted version
          try { localStorage.removeItem(`draft:${decisionId}:${selectedName}`); } catch {}
        } else {
          // No server response — restore draft if available
          try {
            const saved = localStorage.getItem(`draft:${decisionId}:${selectedName}`);
            if (saved) {
              setAnswers(JSON.parse(saved));
            } else {
              setAnswers({});
            }
          } catch {
            setAnswers({});
          }
          setSubmitted(false);
        }
      })
      .catch(() => {
        setAnswers({});
        setSubmitted(false);
      })
      .finally(() => setLoadingExisting(false));
  }, [selectedName, decisionId]);

  const handleSelectOption = (questionId: string, option: string) => {
    setSubmitted(false);
    setAnswers((prev) => ({
      ...prev,
      [questionId]: {
        ...prev[questionId],
        selected: option,
        reasoning: prev[questionId]?.reasoning ?? "",
      },
    }));
  };

  const handleReasoningChange = (questionId: string, reasoning: string) => {
    setSubmitted(false);
    setAnswers((prev) => ({
      ...prev,
      [questionId]: {
        ...prev[questionId],
        reasoning,
        selected: prev[questionId]?.selected ?? "",
      },
    }));
  };

  const handleSubmit = async () => {
    if (!selectedName || !decision) return;
    const answeredQuestions = decision.questions.filter(
      (q) => answers[q.id]?.selected
    );
    if (answeredQuestions.length === 0) {
      alert("Please answer at least one question before submitting.");
      return;
    }
    // Check reasoning is filled for all answered main questions
    const mainQsMissingReasoning = decision.questions.filter(
      (q) => /^q\d+$/.test(q.id) && answers[q.id]?.selected && !answers[q.id]?.reasoning?.trim()
    );
    if (mainQsMissingReasoning.length > 0) {
      alert(`Please provide reasoning for: ${mainQsMissingReasoning.map(q => q.header).join(", ")}`);
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: selectedName,
          decisionId,
          answers,
        }),
      });
      if (res.ok) {
        setSubmitted(true);
        try { localStorage.removeItem(draftKey); } catch {}
      } else {
        alert("Failed to submit. Try again.");
      }
    } catch {
      alert("Network error. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingDecision) {
    return (
      <div className="min-h-screen bg-[#1a1a2e] flex items-center justify-center">
        <p className="text-zinc-500 text-sm">Loading...</p>
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

  const isClosed = decision.status === "closed";
  const answeredCount = decision.questions.filter(
    (q) => answers[q.id]?.selected
  ).length;
  const totalQuestions = decision.questions.length;

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
            <span>{decisionId}</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-zinc-100">
              {decision.title}
            </h1>
            {isClosed && (
              <span className="inline-flex items-center rounded-full bg-zinc-800 px-2.5 py-0.5 text-[10px] font-medium text-zinc-500 ring-1 ring-inset ring-zinc-700/50">
                Closed
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-zinc-300">
            {decision.description}
          </p>
          {isClosed && (
            <p className="mt-2 text-xs text-amber-400/80">
              This decision is closed. Voting is disabled.
            </p>
          )}
        </div>

        {/* Full markdown context */}
        {decision.markdownContent && (
          <div className="mb-6">
            <MarkdownViewer content={decision.markdownContent} />
          </div>
        )}

        {!isClosed && (
          <>
            {/* Name selector */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-zinc-300 mb-2">
                Select your name
              </label>
              <NameSelector selected={selectedName} onSelect={(name) => {
                setSelectedName(name);
                try { localStorage.setItem("lastVoterName", name); } catch {}
              }} team={decision.team} />
            </div>

            {selectedName && (
              <>
                {loadingExisting ? (
                  <div className="text-center py-12 text-zinc-500 text-sm">
                    Loading...
                  </div>
                ) : (
                  <>
                    {/* Progress bar */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between text-xs text-zinc-300 mb-1.5">
                        <span>
                          {answeredCount}/{totalQuestions} answered
                        </span>
                        <span>
                          {Math.round(
                            (answeredCount / totalQuestions) * 100
                          )}
                          %
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                          style={{
                            width: `${(answeredCount / totalQuestions) * 100}%`,
                          }}
                        />
                      </div>
                    </div>

                    {/* Questions */}
                    <DecisionSection
                      decision={decision}
                      answers={answers}
                      onSelectOption={handleSelectOption}
                      onReasoningChange={handleReasoningChange}
                    />

                    {/* Submit */}
                    <div className="mt-8 flex items-center gap-4">
                      <button
                        onClick={handleSubmit}
                        disabled={submitting || submitted}
                        className={`rounded-lg px-6 py-2.5 text-sm font-medium transition-all duration-200 cursor-pointer ${
                          submitted
                            ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/30"
                            : submitting
                              ? "bg-zinc-700 text-zinc-400 cursor-wait"
                              : "bg-indigo-500 text-white hover:bg-indigo-400 shadow-[0_0_12px_rgba(99,102,241,0.3)]"
                        }`}
                      >
                        {submitted
                          ? "Submitted"
                          : submitting
                            ? "Submitting..."
                            : "Submit Votes"}
                      </button>
                      {submitted && (
                        <span className="text-xs text-zinc-400">
                          Your responses have been saved. You can edit and
                          resubmit.
                        </span>
                      )}
                    </div>
                  </>
                )}
              </>
            )}
          </>
        )}

        {/* Footer links */}
        <div className="mt-6 mb-4 flex items-center justify-center gap-4">
          <Link
            href="/"
            className="text-xs text-zinc-400 hover:text-indigo-300 transition-colors"
          >
            ← All decisions
          </Link>
          <Link
            href={`/results/${decisionId}`}
            className="text-xs text-zinc-400 hover:text-indigo-300 transition-colors"
          >
            View results →
          </Link>
        </div>
      </div>
    </div>
  );
}
