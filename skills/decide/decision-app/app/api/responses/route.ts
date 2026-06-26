import { NextResponse } from "next/server";
import { getResponse, getAllResponses } from "@/lib/kv";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const name = searchParams.get("name");
    const decisionId = searchParams.get("decisionId");

    if (name && decisionId) {
      const response = await getResponse(decisionId, name);
      return NextResponse.json({ response });
    }

    const responses = await getAllResponses(decisionId ?? undefined);
    return NextResponse.json({ responses });
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
