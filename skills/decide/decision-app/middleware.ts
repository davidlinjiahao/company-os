import { NextRequest, NextResponse } from "next/server";

const PASSWORD = process.env.DECIDE_PASSWORD;
const COOKIE_NAME = "auth_token";

function getAuthValue(): string {
  if (!PASSWORD) throw new Error("DECIDE_PASSWORD env var is required");
  const { createHmac } = require("crypto");
  return createHmac("sha256", PASSWORD).update("decide-auth").digest("hex").slice(0, 32);
}

export function middleware(request: NextRequest) {
  if (!PASSWORD) {
    return NextResponse.json({ error: "DECIDE_PASSWORD not configured" }, { status: 503 });
  }

  const authCookie = request.cookies.get(COOKIE_NAME);
  if (authCookie?.value === getAuthValue()) {
    return NextResponse.next();
  }

  // Allow the password page and its API
  if (request.nextUrl.pathname === "/login") {
    return NextResponse.next();
  }
  if (
    request.nextUrl.pathname === "/api/login" &&
    request.method === "POST"
  ) {
    return NextResponse.next();
  }

  // Redirect to login
  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("from", request.nextUrl.pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    /*
     * Match all paths except static files and Next.js internals
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
