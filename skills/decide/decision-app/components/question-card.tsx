"use client";

import { OptionPill } from "./option-pill";
import type { Question } from "@/lib/decisions";

interface QuestionCardProps {
  question: Question;
  selectedOption: string | null;
  reasoning: string;
  onSelectOption: (option: string) => void;
  onReasoningChange: (reasoning: string) => void;
  showReasoning?: boolean;
}

export function QuestionCard({
  question,
  selectedOption,
  reasoning,
  onSelectOption,
  onReasoningChange,
  showReasoning = true,
}: QuestionCardProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2.5">
        <span className="inline-flex items-center rounded-md bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-300 ring-1 ring-inset ring-zinc-700/50">
          {question.header}
        </span>
        <h3 className="text-sm font-medium text-zinc-100">
          {question.question}
        </h3>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {question.options.map((opt) => (
          <OptionPill
            key={opt.label}
            label={opt.label}
            description={opt.description}
            selected={selectedOption === opt.label}
            onClick={() => onSelectOption(opt.label)}
          />
        ))}
      </div>
      {showReasoning && (
        <textarea
          value={reasoning}
          onChange={(e) => onReasoningChange(e.target.value)}
          placeholder="Required: explain your reasoning..."
          rows={4}
          className="w-full resize-none rounded-lg border border-zinc-700/50 bg-zinc-900/50 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-400 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 transition-colors"
        />
      )}
    </div>
  );
}
