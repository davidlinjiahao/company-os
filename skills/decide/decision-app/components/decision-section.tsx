"use client";

import { QuestionCard } from "./question-card";
import type { Decision } from "@/lib/decisions";

interface DecisionSectionProps {
  decision: Decision;
  answers: Record<string, { selected: string; reasoning: string }>;
  onSelectOption: (questionId: string, option: string) => void;
  onReasoningChange: (questionId: string, reasoning: string) => void;
}

export function DecisionSection({
  decision,
  answers,
  onSelectOption,
  onReasoningChange,
}: DecisionSectionProps) {
  return (
    <section className="rounded-xl border border-zinc-800/80 bg-[#16213e]/40 p-5 sm:p-6 space-y-6">
      <div>
        <h2 className="text-base font-semibold text-zinc-100">
          {decision.title}
        </h2>
        <p className="mt-1 text-sm text-zinc-300 leading-relaxed">
          {decision.description}
        </p>
      </div>
      <div className="space-y-6">
        {decision.questions.map((q) => {
          // Show reasoning only for main questions (q1, q2, ...) not sub-questions (q3a, q5b, ...)
          const isMainQuestion = /^q\d+$/.test(q.id);
          return (
            <QuestionCard
              key={q.id}
              question={q}
              selectedOption={answers[q.id]?.selected ?? null}
              reasoning={answers[q.id]?.reasoning ?? ""}
              onSelectOption={(opt) => onSelectOption(q.id, opt)}
              onReasoningChange={(r) => onReasoningChange(q.id, r)}
              showReasoning={isMainQuestion}
            />
          );
        })}
      </div>
    </section>
  );
}
