import { NextResponse } from "next/server";
import { getAllDecisions } from "@/lib/decisions-store";
import { getAllResponses } from "@/lib/kv";

export async function GET() {
  try {
    const decisions = await getAllDecisions();
    const allResponses = await getAllResponses();

    const result = decisions.map((d) => {
      const votes = allResponses.filter((r) => r.decisionId === d.id);
      return {
        id: d.id,
        title: d.title,
        description: d.description,
        status: d.status,
        questionCount: d.questions.length,
        voteCount: votes.length,
        voters: votes.map((v) => v.name),
        team: d.team,
      };
    });

    return NextResponse.json({ decisions: result });
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
