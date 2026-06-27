import { NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { getDecision, saveSynthesis, getSynthesis, deleteSynthesis } from "@/lib/decisions-store";
import { getAllResponses } from "@/lib/kv";

const client = new Anthropic();

export async function GET(
  request: Request,
  { params }: { params: Promise<{ decisionId: string }> }
) {
  try {
    const { decisionId } = await params;
    const url = new URL(request.url);
    const regenerate = url.searchParams.get("regenerate") === "true";
    const decision = await getDecision(decisionId);

    if (!decision) {
      return NextResponse.json(
        { error: "Decision not found" },
        { status: 404 }
      );
    }

    if (regenerate) {
      await deleteSynthesis(decisionId);
    }

    // Check for cached synthesis first
    if (!regenerate) {
      const cached = await getSynthesis(decisionId);
      if (cached) {
        return NextResponse.json({ conclusion: cached });
      }
    }

    const responses = await getAllResponses(decisionId);

    if (responses.length === 0) {
      return NextResponse.json(
        { error: "No votes to analyze" },
        { status: 400 }
      );
    }

    // Build context for Claude
    const voteData = decision.questions.map((q) => {
      const tally: Record<string, { voters: string[]; reasonings: string[] }> = {};

      for (const r of responses) {
        const answer = r.answers[q.id];
        if (answer?.selected) {
          if (!tally[answer.selected]) {
            tally[answer.selected] = { voters: [], reasonings: [] };
          }
          tally[answer.selected].voters.push(r.name);
          if (answer.reasoning) {
            tally[answer.selected].reasonings.push(`${r.name}: ${answer.reasoning}`);
          }
        }
      }

      const sorted = Object.entries(tally).sort(
        (a, b) => b[1].voters.length - a[1].voters.length
      );

      return {
        question: q.question,
        header: q.header,
        options: q.options.map((o) => o.label),
        votes: sorted.map(([option, data]) => ({
          option,
          count: data.voters.length,
          voters: data.voters,
          reasonings: data.reasonings,
        })),
        totalVotes: responses.length,
      };
    });

    const documentContext = decision.markdownContent
      ? `\n## Full Decision Document\n\n${decision.markdownContent}\n`
      : "";

    const prompt = `You are the Council, a synthesis agent that analyzes team votes, reasoning, and the full decision document to surface the clearest path forward.

Analyze this team decision and provide a final recommendation:

## Decision: ${decision.title}
${decision.description}
${documentContext}
## Team Votes (${responses.length} members voted: ${responses.map((r) => r.name).join(", ")})

${voteData
  .map(
    (q) => `### ${q.header}: ${q.question}
${q.votes
  .map(
    (v) =>
      `- ${v.option} (${v.count}/${q.totalVotes}): ${v.voters.join(", ")}${
        v.reasonings.length > 0 ? `\n  Reasoning:\n${v.reasonings.map((r) => `    - ${r}`).join("\n")}` : ""
      }`
  )
  .join("\n")}`
  )
  .join("\n\n")}

---

Provide your synthesis in this format. Do NOT use bold/asterisk formatting anywhere in your output — write in plain text only.

## Overall Recommendation
[2-3 sentence summary of what the team should do]

## Per-Question Conclusions
${decision.questions.map((q) => `### ${q.header}\n[1-2 sentences on the recommended choice and why]`).join("\n\n")}

## Key Considerations
[Bullet points of important factors the team should keep in mind]

## Dissenting Views
[Acknowledge any minority opinions that deserve consideration]

Be direct and actionable.`;

    const message = await client.messages.create({
      model: "claude-opus-4-6",
      max_tokens: 3000,
      messages: [{ role: "user", content: prompt }],
    });

    const conclusion =
      message.content[0].type === "text" ? message.content[0].text : "";

    // Cache the synthesis
    if (conclusion) {
      await saveSynthesis(decisionId, conclusion);
    }

    return NextResponse.json({ conclusion });
  } catch (error) {
    console.error("Conclude API error:", error);
    return NextResponse.json(
      { error: "Failed to generate conclusion" },
      { status: 500 }
    );
  }
}
