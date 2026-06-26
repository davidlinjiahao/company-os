import { createHmac } from "crypto";
import { NextRequest, NextResponse } from "next/server";

const PASSWORD = process.env.DECIDE_PASSWORD;

function getAuthValue(): string {
  if (!PASSWORD) throw new Error("DECIDE_PASSWORD env var is required");
  return createHmac("sha256", PASSWORD).update("decide-auth").digest("hex").slice(0, 32);
}

export async function POST(request: NextRequest) {
  if (!PASSWORD) {
    return NextResponse.json({ error: "DECIDE_PASSWORD not configured" }, { status: 503 });
  }

  const { password } = await request.json();

  if (password === PASSWORD) {
    const response = NextResponse.json({ ok: true });
    response.cookies.set("auth_token", getAuthValue(), {
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });
    return response;
  }

  return NextResponse.json({ error: "Incorrect password" }, { status: 401 });
}
