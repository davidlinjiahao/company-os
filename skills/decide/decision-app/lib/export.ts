import type { Decision } from "./decisions";
import type { VoteResponse } from "./kv";

export function generatePersonMarkdown(decisions: Decision[], response: VoteResponse): string {
  const lines: string[] = [];
  lines.push(`# ${response.name} - Decision Responses`);
  lines.push(`## Date: ${new Date(response.submittedAt).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}`);
  lines.push("");

  for (const decision of decisions) {
    lines.push(`### ${decision.title}`);
    lines.push("");
    for (const q of decision.questions) {
      const answer = response.answers[q.id];
      if (answer) {
        const reasoning = answer.reasoning ? ` — ${answer.reasoning}` : "";
        lines.push(`- **${q.header}**: ${answer.selected}${reasoning}`);
      } else {
        lines.push(`- **${q.header}**: *(no response)*`);
      }
    }
    lines.push("");
  }

  return lines.join("\n");
}

export function generateSummaryMarkdown(decisions: Decision[], responses: VoteResponse[]): string {
  const lines: string[] = [];
  lines.push("# Decision Summary - Vote Results");
  lines.push(`## Date: ${new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}`);
  lines.push(`## Participants: ${responses.map((r) => r.name).join(", ")}`);
  lines.push("");

  for (const decision of decisions) {
    lines.push(`---`);
    lines.push(`## ${decision.title}`);
    lines.push(`> ${decision.description}`);
    lines.push("");

    for (const q of decision.questions) {
      lines.push(`### ${q.header}: ${q.question}`);
      lines.push("");

      // Tally votes
      const tally: Record<string, string[]> = {};
      for (const r of responses) {
        const answer = r.answers[q.id];
        if (answer) {
          if (!tally[answer.selected]) tally[answer.selected] = [];
          tally[answer.selected].push(r.name);
        }
      }

      // Sort by vote count
      const sorted = Object.entries(tally).sort(
        (a, b) => b[1].length - a[1].length
      );

      // Consensus check
      const totalVotes = responses.length;
      const topVotes = sorted[0]?.[1].length ?? 0;
      let consensusTag = "";
      if (topVotes >= Math.ceil(totalVotes * 0.75)) {
        consensusTag = " CONSENSUS";
      } else if (topVotes >= Math.ceil(totalVotes * 0.5)) {
        consensusTag = " MAJORITY";
      } else {
        consensusTag = " SPLIT";
      }

      lines.push(`**Result:**${consensusTag}`);
      lines.push("");

      for (const [option, voters] of sorted) {
        lines.push(
          `- **${option}** (${voters.length}/${totalVotes}): ${voters.join(", ")}`
        );
      }
      lines.push("");

      // Include reasoning
      const reasonings: string[] = [];
      for (const r of responses) {
        const answer = r.answers[q.id];
        if (answer?.reasoning) {
          reasonings.push(`  - **${r.name}**: ${answer.reasoning}`);
        }
      }
      if (reasonings.length > 0) {
        lines.push("**Reasoning:**");
        lines.push(...reasonings);
        lines.push("");
      }
    }
  }

  return lines.join("\n");
}

export function generateFullReportMarkdown(
  decision: Decision,
  responses: VoteResponse[],
  synthesis?: string
): string {
  const lines: string[] = [];
  const date = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const participants = responses.map((r) => r.name).join(", ");

  lines.push(`# ${decision.title}`);
  lines.push("");
  lines.push(`**Date:** ${date}`);
  lines.push(`**Participants:** ${participants} (${responses.length}/${decision.team.length})`);
  lines.push(`**Status:** ${decision.status}`);
  lines.push("");

  // Original markdown context
  if (decision.markdownContent) {
    lines.push("---");
    lines.push("");
    lines.push("## Original Decision Context");
    lines.push("");
    lines.push(decision.markdownContent);
    lines.push("");
  }

  // Vote results
  lines.push("---");
  lines.push("");
  lines.push("## Vote Results");
  lines.push("");

  for (const q of decision.questions) {
    lines.push(`### ${q.header}: ${q.question}`);
    lines.push("");

    const tally: Record<string, string[]> = {};
    for (const r of responses) {
      const answer = r.answers[q.id];
      if (answer?.selected) {
        if (!tally[answer.selected]) tally[answer.selected] = [];
        tally[answer.selected].push(r.name);
      }
    }

    const sorted = Object.entries(tally).sort(
      (a, b) => b[1].length - a[1].length
    );

    const totalVotes = responses.length;
    const topVotes = sorted[0]?.[1].length ?? 0;
    let tag = "SPLIT";
    if (topVotes >= Math.ceil(totalVotes * 0.75)) tag = "CONSENSUS";
    else if (topVotes >= Math.ceil(totalVotes * 0.5)) tag = "MAJORITY";

    lines.push(`**Result:** ${tag}`);
    lines.push("");

    for (const [option, voters] of sorted) {
      lines.push(`- **${option}** (${voters.length}/${totalVotes}): ${voters.join(", ")}`);
    }
    lines.push("");

    const fullReasonings: string[] = [];
    for (const r of responses) {
      const answer = r.answers[q.id];
      if (answer?.reasoning) {
        fullReasonings.push(`  - **${r.name}**: ${answer.reasoning}`);
      }
    }
    if (fullReasonings.length > 0) {
      lines.push("**Reasoning:**");
      lines.push(...fullReasonings);
      lines.push("");
    }
  }

  // AI Synthesis
  if (synthesis) {
    lines.push("---");
    lines.push("");
    lines.push("## Council Synthesis");
    lines.push("");
    lines.push(synthesis);
    lines.push("");
  }

  return lines.join("\n");
}
