"use client";

import { useState, useEffect, useRef, useCallback } from "react";
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

interface ExtractedQuestion {
  id: string;
  header: string;
  question: string;
  options: { label: string; description: string }[];
}

interface UploadResult {
  decision: {
    id: string;
    title: string;
    description: string;
    questionCount: number;
    questions: ExtractedQuestion[];
  };
  shareUrl: string;
}

type UploadPhase = "idle" | "preview" | "extracting" | "review" | "confirmed";

export default function AdminPage() {
  const [decisions, setDecisions] = useState<DecisionSummary[]>([]);
  const [loadingDecisions, setLoadingDecisions] = useState(true);

  // Upload state
  const [phase, setPhase] = useState<UploadPhase>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string>("");
  const [dragOver, setDragOver] = useState(false);
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch("/api/decisions")
      .then((res) => res.json())
      .then((data) => setDecisions(data.decisions ?? []))
      .catch(() => setDecisions([]))
      .finally(() => setLoadingDecisions(false));
  }, []);

  const handleFile = useCallback(async (f: File) => {
    if (!f.name.endsWith(".md")) {
      setError("Only .md files are accepted");
      return;
    }
    setError("");
    setFile(f);
    const text = await f.text();
    setFileContent(text);
    setPhase("preview");
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const handleUpload = async () => {
    if (!file) return;
    setPhase("extracting");
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("createdBy", "admin");

      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        const detail = data.detail ? ` (${data.detail})` : "";
        setError((data.error || "Upload failed") + detail);
        setPhase("preview");
        return;
      }

      setUploadResult(data);
      setPhase("review");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Network error";
      setError(`Connection failed: ${msg}. Try again.`);
      setPhase("preview");
    }
  };

  const handleConfirm = () => {
    setPhase("confirmed");
    // Refresh decision list
    fetch("/api/decisions")
      .then((res) => res.json())
      .then((data) => setDecisions(data.decisions ?? []));
  };

  const handleReset = () => {
    setPhase("idle");
    setFile(null);
    setFileContent("");
    setUploadResult(null);
    setError("");
    setCopied(false);
  };

  const copyShareLink = () => {
    if (!uploadResult) return;
    const url = `${window.location.origin}${uploadResult.shareUrl}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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
            <span>admin</span>
          </div>
          <h1 className="text-xl font-semibold text-zinc-100">
            Upload Decision
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Upload an Obsidian .md decision document to create a new votable decision.
          </p>
        </div>

        {/* Upload zone */}
        {phase === "idle" && (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`rounded-xl border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-200 ${
              dragOver
                ? "border-indigo-500 bg-indigo-500/5"
                : "border-zinc-700/50 bg-[#16213e]/20 hover:border-zinc-600 hover:bg-[#16213e]/30"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".md"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
            <div className="text-zinc-400 text-3xl mb-3">
              {dragOver ? "+" : "^"}
            </div>
            <p className="text-sm text-zinc-300">
              {dragOver
                ? "Drop .md file here"
                : "Drag & drop a .md file, or click to browse"}
            </p>
            <p className="text-xs text-zinc-500 mt-2">
              Obsidian decision documents only
            </p>
          </div>
        )}

        {/* Preview */}
        {phase === "preview" && (
          <div className="space-y-4">
            <div className="rounded-xl border border-zinc-800/80 bg-[#16213e]/40 p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-zinc-200">
                  {file?.name}
                </h3>
                <span className="text-xs text-zinc-400">
                  {Math.round((fileContent.length / 1024) * 10) / 10} KB
                </span>
              </div>
              <div className="max-h-80 overflow-y-auto rounded-lg bg-zinc-900/50 p-4 border border-zinc-800/50">
                <pre className="text-xs text-zinc-400 whitespace-pre-wrap font-mono leading-relaxed">
                  {fileContent}
                </pre>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleUpload}
                className="rounded-lg bg-indigo-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-400 transition-colors shadow-[0_0_12px_rgba(99,102,241,0.3)] cursor-pointer"
              >
                Upload & Extract Questions
              </button>
              <button
                onClick={handleReset}
                className="rounded-lg px-4 py-2.5 text-sm font-medium text-zinc-400 ring-1 ring-zinc-700/50 hover:bg-zinc-800 transition-colors cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Extracting */}
        {phase === "extracting" && (
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-8 text-center">
            <div className="inline-flex items-center gap-3">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              <p className="text-sm text-indigo-400">
                Extracting questions with Claude...
              </p>
            </div>
            <p className="text-xs text-zinc-500 mt-2">
              This may take a few seconds
            </p>
          </div>
        )}

        {/* Review extracted questions */}
        {phase === "review" && uploadResult && (
          <div className="space-y-4">
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-5">
              <h3 className="text-base font-semibold text-zinc-100 mb-1">
                {uploadResult.decision.title}
              </h3>
              <p className="text-sm text-zinc-300 mb-4">
                {uploadResult.decision.description}
              </p>

              <div className="space-y-3">
                {uploadResult.decision.questions.map((q, i) => (
                  <div
                    key={q.id}
                    className="rounded-lg bg-zinc-900/30 border border-zinc-800/50 p-3"
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-[10px] font-medium text-zinc-500">
                        Q{i + 1}
                      </span>
                      <span className="inline-flex items-center rounded-md bg-zinc-800 px-2 py-0.5 text-[10px] font-medium text-zinc-400 ring-1 ring-inset ring-zinc-700/50">
                        {q.header}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-200 mb-2">{q.question}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {q.options.map((opt) => (
                        <span
                          key={opt.label}
                          className="inline-flex items-center rounded-full bg-zinc-800/50 px-2.5 py-0.5 text-[10px] text-zinc-400"
                        >
                          {opt.label}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleConfirm}
                className="rounded-lg bg-emerald-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-emerald-400 transition-colors cursor-pointer"
              >
                Confirm & Create
              </button>
              <button
                onClick={handleReset}
                className="rounded-lg px-4 py-2.5 text-sm font-medium text-zinc-400 ring-1 ring-zinc-700/50 hover:bg-zinc-800 transition-colors cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Confirmed — show share link */}
        {phase === "confirmed" && uploadResult && (
          <div className="space-y-4">
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-5 text-center">
              <p className="text-emerald-400 text-sm font-medium mb-3">
                Decision created successfully
              </p>
              <div className="flex items-center justify-center gap-2">
                <code className="rounded-lg bg-zinc-900/50 px-4 py-2 text-sm text-zinc-200 font-mono border border-zinc-800/50">
                  {uploadResult.shareUrl}
                </code>
                <button
                  onClick={copyShareLink}
                  className="rounded-lg bg-zinc-800 px-3 py-2 text-xs font-medium text-zinc-300 hover:bg-zinc-700 transition-colors ring-1 ring-zinc-700/50 cursor-pointer"
                >
                  {copied ? "Copied!" : "Copy link"}
                </button>
              </div>
              <div className="mt-4 flex items-center justify-center gap-3">
                <Link
                  href={uploadResult.shareUrl}
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  Go to vote page →
                </Link>
                <button
                  onClick={handleReset}
                  className="text-xs text-zinc-500 hover:text-zinc-400 transition-colors cursor-pointer"
                >
                  Upload another
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-lg bg-rose-500/10 border border-rose-500/20 px-4 py-3">
            <p className="text-sm text-rose-300">{error}</p>
            {file && phase === "preview" && (
              <button
                onClick={handleUpload}
                className="mt-2 text-xs text-rose-400 hover:text-rose-300 underline underline-offset-2 cursor-pointer"
              >
                Retry upload
              </button>
            )}
          </div>
        )}

        {/* Existing decisions list */}
        <div className="mt-10">
          <h2 className="text-base font-semibold text-zinc-100 mb-4">
            Existing Decisions
          </h2>
          {loadingDecisions ? (
            <p className="text-zinc-400 text-sm">Loading...</p>
          ) : decisions.length === 0 ? (
            <p className="text-zinc-400 text-sm">No decisions yet.</p>
          ) : (
            <div className="space-y-2">
              {decisions.map((d) => (
                <div
                  key={d.id}
                  className="rounded-lg border border-zinc-800/50 bg-[#16213e]/20 p-3 flex items-center justify-between"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-zinc-200 truncate">
                        {d.title}
                      </span>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                          d.status === "active"
                            ? "bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20"
                            : "bg-zinc-800 text-zinc-500 ring-1 ring-inset ring-zinc-700/50"
                        }`}
                      >
                        {d.status}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 mt-0.5">
                      {d.questionCount} questions · {d.voteCount}/{d.team.length}{" "}
                      voted
                    </p>
                  </div>
                  <div className="flex gap-2 shrink-0 ml-3">
                    <Link
                      href={`/vote/${d.id}`}
                      className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      Vote
                    </Link>
                    <Link
                      href={`/results/${d.id}`}
                      className="text-xs text-zinc-400 hover:text-zinc-300 transition-colors"
                    >
                      Results
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <Link
            href="/"
            className="text-xs text-zinc-400 hover:text-indigo-300 transition-colors"
          >
            ← Back to decisions
          </Link>
        </div>
      </div>
    </div>
  );
}
