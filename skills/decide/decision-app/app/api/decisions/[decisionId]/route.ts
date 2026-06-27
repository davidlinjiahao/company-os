import { NextResponse } from "next/server";
import { getDecision } from "@/lib/decisions-store";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ decisionId: string }> }
) {
  try {
    const { decisionId } = await params;
    const decision = await getDecision(decisionId);

    if (!decision) {
      return NextResponse.json(
        { error: "Decision not found" },
        { status: 404 }
      );
    }

    return NextResponse.json({ decision });
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
