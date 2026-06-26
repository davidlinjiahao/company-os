import { NextResponse } from "next/server";
import { saveResponse } from "@/lib/kv";
import { getDecision } from "@/lib/decisions-store";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { name, decisionId, answers } = body;

    if (!name || typeof name !== "string" || name.trim().length === 0) {
      return NextResponse.json({ error: "Name is required" }, { status: 400 });
    }

    const decision = await getDecision(decisionId);
    if (!decisionId || !decision) {
      return NextResponse.json({ error: "Invalid decisionId" }, { status: 400 });
    }

    if (!answers || typeof answers !== "object") {
      return NextResponse.json({ error: "Invalid answers" }, { status: 400 });
    }

    await saveResponse({
      name: name.trim(),
      decisionId,
      answers,
      submittedAt: new Date().toISOString(),
    });

    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
