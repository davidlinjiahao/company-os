import Anthropic from "@anthropic-ai/sdk";
import { DEFAULT_TEAM, type Decision } from "./decisions";

const client = new Anthropic();

/**
 * Uses Claude to extract structured voting questions from a markdown decision document.
 * Decision docs following our template have a "Decision Questions for the Team" section
 * with 10 questions (and sub-questions) from Decision Making Principles. This function
 * extracts ALL of them as votable questions with options derived from the document context.
 */
export async function extractQuestionsFromMarkdown(
  fileName: string,
  content: string
): Promise<Omit<Decision, "markdownContent" | "createdAt" | "createdBy">> {
  const baseName = fileName.replace(/\.md$/, "");

  const prompt = `You are parsing a structured decision document for a team voting app.

Document: ${baseName}
---
${content}
---

This document follows a decision-making template. It has a "Decision Questions for the Team" section near the end with numbered questions (1-10) and sub-questions (3a, 4a-4c, 5a-5c, etc.) based on Decision Making Principles.

Your job is to extract ALL of these existing questions as votable items. Do NOT invent new questions — use the ones already in the document.

For each question:
- Use the exact question text from the document
- Create 2-4 answer options based on the context provided under that question in the document
- The options should reflect the specific choices/perspectives mentioned (e.g. "India quantity" vs "SF quality")
- For sub-questions, include them as separate votable questions with their parent number as prefix (e.g. "4a", "5b")
- Keep the option descriptions concise (1 sentence)

Also extract the document title and a brief description from the top of the document.

Respond with ONLY valid JSON (no markdown code fences, no explanation, no text before or after):
{
  "title": "Decision: [short title from the document]",
  "description": "[1-2 sentence summary from the document]",
  "status": "active",
  "context": "[brief context paragraph]",
  "questions": [
    {
      "id": "q1",
      "header": "Q1",
      "question": "[exact question text from the document]",
      "options": [
        {"label": "[option]", "description": "[1 sentence from document context]"},
        {"label": "[option]", "description": "[1 sentence from document context]"}
      ]
    },
    {
      "id": "q3a",
      "header": "Q3a",
      "question": "[sub-question text]",
      "options": [...]
    }
  ]
}

Rules:
- Extract EVERY numbered question and sub-question from the "Decision Questions" section
- Typically this means 10 main questions + ~15 sub-questions = ~25 total questions
- Options must come from the document's own analysis, not invented
- If a question is open-ended with no clear options in the document, use: "Yes", "No", "Needs more discussion"
- For question 10 ("What is your single decisive reason?"), use the specific decisive reasons listed in the document as options
- If there is no "Decision Questions" section, look for any numbered questions or decision points in the document and extract those instead
- If the document isn't actually a decision doc, return {"skip": true}`;

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 16000,
    messages: [{ role: "user", content: prompt }],
  });

  const responseText =
    message.content[0].type === "text" ? message.content[0].text : "";

  if (!responseText.trim()) {
    throw new Error("Claude returned an empty response");
  }

  // Strip markdown code fences if present
  let cleaned = responseText.trim();
  cleaned = cleaned.replace(/^```(?:json)?\s*\n?/i, "").replace(/\n?```\s*$/i, "");

  // Find outermost JSON object
  const firstBrace = cleaned.indexOf("{");
  const lastBrace = cleaned.lastIndexOf("}");
  if (firstBrace === -1 || lastBrace === -1 || lastBrace <= firstBrace) {
    throw new Error(
      `No JSON object found in Claude response. First 200 chars: ${responseText.slice(0, 200)}`
    );
  }

  const jsonStr = cleaned.slice(firstBrace, lastBrace + 1);

  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(jsonStr);
  } catch (e) {
    throw new Error(
      `Failed to parse JSON from Claude response: ${(e as Error).message}. First 300 chars: ${jsonStr.slice(0, 300)}`
    );
  }

  if (parsed.skip) {
    throw new Error("Document was not recognized as a decision document by Claude");
  }

  const questions = parsed.questions;
  if (!Array.isArray(questions) || questions.length === 0) {
    throw new Error(
      `Claude returned 0 questions. Parsed keys: ${Object.keys(parsed).join(", ")}`
    );
  }

  // Generate ID from filename
  const id = baseName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 50);

  return {
    id,
    title: (parsed.title as string) || `Decision: ${baseName}`,
    description: (parsed.description as string) || "",
    source: baseName,
    status: (parsed.status as "active" | "closed") || "active",
    team: [...DEFAULT_TEAM],
    context: (parsed.context as string) || "",
    questions: questions.map(
      (q: { id: string; header: string; question: string; options: { label: string; description: string }[] }, i: number) => ({
        id: q.id || `q${i + 1}`,
        header: q.header || `Q${i + 1}`,
        question: q.question,
        options: q.options || [],
      })
    ),
  };
}
