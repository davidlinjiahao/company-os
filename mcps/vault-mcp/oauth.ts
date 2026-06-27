import { createHash, randomUUID } from "crypto";

// --- Config ---

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID ?? "";
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET ?? "";
// Optional Google Workspace domain to restrict OAuth to (e.g. "yourco.com").
// Leave unset to allow any verified Google account — the emails.json allowlist
// (EMAIL_MAP) is the primary authorization gate regardless.
const ALLOWED_HD = process.env.GOOGLE_WORKSPACE_DOMAIN ?? "";

// --- Email-to-username mapping ---

const EMAILS_PATH = import.meta.dir + "/emails.json";
let EMAIL_MAP: Record<string, string> = {};
try {
  EMAIL_MAP = JSON.parse(await Bun.file(EMAILS_PATH).text());
} catch {
  console.warn("[oauth] emails.json not found — Google OAuth disabled");
}

// --- Types ---

interface ClientInfo {
  client_id: string;
  redirect_uris: string[];
  client_name?: string;
}

interface AuthCode {
  codeChallenge: string;
  redirectUri: string;
  email: string;
  clientId: string;
  expiresAt: number;
}

interface AccessToken {
  email: string;
  clientId: string;
  expiresAt: number;
}

interface PendingAuth {
  clientId: string;
  codeChallenge: string;
  redirectUri: string;
  state: string;
}

// --- In-memory stores ---

const clients = new Map<string, ClientInfo>();
const authCodes = new Map<string, AuthCode>();
const accessTokens = new Map<string, AccessToken>();
const pendingGoogleAuths = new Map<string, PendingAuth>();

// --- PKCE ---

function verifyS256(verifier: string, challenge: string): boolean {
  return createHash("sha256").update(verifier).digest("base64url") === challenge;
}

// --- Route handlers ---

export function handleProtectedResourceMetadata(baseUrl: string): Response {
  return Response.json({
    resource: `${baseUrl}/mcp`,
    authorization_servers: [baseUrl],
  });
}

export function handleAuthServerMetadata(baseUrl: string): Response {
  return Response.json({
    issuer: baseUrl,
    authorization_endpoint: `${baseUrl}/authorize`,
    token_endpoint: `${baseUrl}/token`,
    registration_endpoint: `${baseUrl}/register`,
    response_types_supported: ["code"],
    grant_types_supported: ["authorization_code"],
    code_challenge_methods_supported: ["S256"],
    token_endpoint_auth_methods_supported: ["none"],
  });
}

export async function handleRegister(req: Request): Promise<Response> {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "invalid_request" }, { status: 400 });
  }

  const clientId = randomUUID();
  const redirectUris = Array.isArray(body.redirect_uris) ? (body.redirect_uris as string[]) : [];
  const client: ClientInfo = {
    client_id: clientId,
    redirect_uris: redirectUris,
    client_name: typeof body.client_name === "string" ? body.client_name : undefined,
  };
  clients.set(clientId, client);

  return Response.json(
    { client_id: clientId, client_id_issued_at: Math.floor(Date.now() / 1000), ...client },
    { status: 201 },
  );
}

export function handleAuthorize(req: Request, baseUrl: string): Response {
  const url = new URL(req.url);
  const clientId = url.searchParams.get("client_id");
  const redirectUri = url.searchParams.get("redirect_uri");
  const codeChallenge = url.searchParams.get("code_challenge");
  const codeChallengeMethod = url.searchParams.get("code_challenge_method");
  const state = url.searchParams.get("state");

  if (!clientId || !clients.has(clientId)) {
    return Response.json({ error: "invalid_client" }, { status: 400 });
  }

  if (!redirectUri || !codeChallenge || codeChallengeMethod !== "S256") {
    return Response.json({ error: "invalid_request", error_description: "PKCE S256 required" }, { status: 400 });
  }

  // Store pending auth keyed by a Google OAuth state param
  const googleState = randomUUID();
  pendingGoogleAuths.set(googleState, { clientId, codeChallenge, redirectUri, state: state ?? "" });

  // Redirect to Google OAuth
  const googleAuthUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  googleAuthUrl.searchParams.set("client_id", GOOGLE_CLIENT_ID);
  googleAuthUrl.searchParams.set("redirect_uri", `${baseUrl}/oauth/google/callback`);
  googleAuthUrl.searchParams.set("response_type", "code");
  googleAuthUrl.searchParams.set("scope", "openid email");
  if (ALLOWED_HD) googleAuthUrl.searchParams.set("hd", ALLOWED_HD);
  googleAuthUrl.searchParams.set("state", googleState);

  return Response.redirect(googleAuthUrl.toString(), 302);
}

export async function handleGoogleCallback(req: Request, baseUrl: string): Promise<Response> {
  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const googleState = url.searchParams.get("state");
  const error = url.searchParams.get("error");

  if (error) {
    return new Response(`Google OAuth error: ${error}`, { status: 400 });
  }

  if (!code || !googleState) {
    return new Response("Missing code or state", { status: 400 });
  }

  const pending = pendingGoogleAuths.get(googleState);
  if (!pending) {
    return new Response("Invalid or expired state", { status: 400 });
  }
  pendingGoogleAuths.delete(googleState);

  // Exchange Google's code for tokens
  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: GOOGLE_CLIENT_ID,
      client_secret: GOOGLE_CLIENT_SECRET,
      redirect_uri: `${baseUrl}/oauth/google/callback`,
      grant_type: "authorization_code",
    }),
  });

  if (!tokenRes.ok) {
    const text = await tokenRes.text();
    console.error("[oauth] Google token exchange failed:", text);
    return new Response("Google token exchange failed", { status: 502 });
  }

  const tokenData = (await tokenRes.json()) as { id_token?: string };
  if (!tokenData.id_token) {
    return new Response("No id_token from Google", { status: 502 });
  }

  // Decode ID token payload (trusted — comes directly from Google's HTTPS endpoint)
  const payload = JSON.parse(atob(tokenData.id_token.split(".")[1])) as {
    email?: string;
    email_verified?: boolean;
    hd?: string;
  };

  if (ALLOWED_HD && payload.hd !== ALLOWED_HD) {
    return new Response(`Access denied: must use an @${ALLOWED_HD} account`, { status: 403 });
  }

  if (!payload.email_verified || !payload.email) {
    return new Response("Email not verified", { status: 403 });
  }

  if (!EMAIL_MAP[payload.email]) {
    return new Response(`Access denied: ${payload.email} is not in the authorized list`, { status: 403 });
  }

  // Generate auth code for Claude Code
  const authCode = randomUUID();
  authCodes.set(authCode, {
    codeChallenge: pending.codeChallenge,
    redirectUri: pending.redirectUri,
    email: payload.email,
    clientId: pending.clientId,
    expiresAt: Date.now() + 5 * 60 * 1000, // 5 min
  });

  // Redirect back to Claude Code's redirect_uri
  const redirectUrl = new URL(pending.redirectUri);
  redirectUrl.searchParams.set("code", authCode);
  if (pending.state) {
    redirectUrl.searchParams.set("state", pending.state);
  }

  return Response.redirect(redirectUrl.toString(), 302);
}

export async function handleToken(req: Request): Promise<Response> {
  let params: URLSearchParams;
  const contentType = req.headers.get("content-type") ?? "";
  if (contentType.includes("application/x-www-form-urlencoded")) {
    params = new URLSearchParams(await req.text());
  } else if (contentType.includes("application/json")) {
    const body = (await req.json()) as Record<string, string>;
    params = new URLSearchParams(body);
  } else {
    params = new URLSearchParams(await req.text());
  }

  const grantType = params.get("grant_type");
  const code = params.get("code");
  const codeVerifier = params.get("code_verifier");
  const redirectUri = params.get("redirect_uri");

  if (grantType !== "authorization_code") {
    return Response.json({ error: "unsupported_grant_type" }, { status: 400 });
  }

  if (!code || !codeVerifier) {
    return Response.json({ error: "invalid_request" }, { status: 400 });
  }

  const authCode = authCodes.get(code);
  if (!authCode) {
    return Response.json({ error: "invalid_grant", error_description: "Unknown code" }, { status: 400 });
  }
  authCodes.delete(code);

  if (authCode.expiresAt < Date.now()) {
    return Response.json({ error: "invalid_grant", error_description: "Code expired" }, { status: 400 });
  }

  if (redirectUri && redirectUri !== authCode.redirectUri) {
    return Response.json({ error: "invalid_grant", error_description: "redirect_uri mismatch" }, { status: 400 });
  }

  if (!verifyS256(codeVerifier, authCode.codeChallenge)) {
    return Response.json({ error: "invalid_grant", error_description: "PKCE verification failed" }, { status: 400 });
  }

  // Issue access token
  const token = randomUUID();
  const expiresIn = 3600; // 1 hour
  accessTokens.set(token, {
    email: authCode.email,
    clientId: authCode.clientId,
    expiresAt: Date.now() + expiresIn * 1000,
  });

  console.log(`[oauth] Issued token for ${authCode.email}`);

  return Response.json({
    access_token: token,
    token_type: "Bearer",
    expires_in: expiresIn,
  });
}

// --- Token verification ---

export function resolveUser(authHeader: string | null): string | null {
  if (!authHeader?.startsWith("Bearer ")) return null;
  const token = authHeader.slice(7);
  const entry = accessTokens.get(token);
  if (!entry) return null;
  if (entry.expiresAt < Date.now()) {
    accessTokens.delete(token);
    return null;
  }
  return EMAIL_MAP[entry.email] ?? null;
}
