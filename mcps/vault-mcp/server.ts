import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { z } from "zod";
import { Database } from "bun:sqlite";
import * as oauth from "./oauth.js";

const PORT = 3131;
const BASE_URL = process.env.VAULT_NGROK_DOMAIN
  ? `https://${process.env.VAULT_NGROK_DOMAIN}`
  : `http://localhost:${PORT}`;

// Load per-user tokens from users.json (token -> username) — optional for legacy auth
const USERS_PATH = import.meta.dir + "/users.json";
let USERS: Record<string, string> = {};
try {
  USERS = JSON.parse(await Bun.file(USERS_PATH).text());
} catch {
  console.warn("[server] users.json not found — legacy token auth disabled");
}

function resolveLegacyUser(authHeader: string | null): string | null {
  if (!authHeader?.startsWith("Bearer ")) return null;
  const token = authHeader.slice(7);
  return USERS[token] ?? null;
}

const DB_PATH = `${process.env.HOME}/.cache/qmd/index.sqlite`;
const ALLOWED_COLLECTIONS = (process.env.VAULT_COLLECTIONS ?? "team-vault").split(",");
const COLLECTION_PLACEHOLDERS = ALLOWED_COLLECTIONS.map(() => "?").join(",");

const db = new Database(DB_PATH, { readonly: true });

function log(user: string, tool: string, details: Record<string, unknown>) {
  console.log(JSON.stringify({ ts: new Date().toISOString(), user, tool, ...details }));
}

// Sanitize FTS5 query: strip special chars, quote each term
function sanitizeQuery(raw: string): string {
  return raw
    .replace(/["""*:^~(){}[\]]/g, "")
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => `"${w}"`)
    .join(" ");
}

const searchStmt = db.prepare(`
  SELECT d.collection, d.path, d.title,
         snippet(documents_fts, 2, '>>>', '<<<', '...', 30) as snippet
  FROM documents_fts
  JOIN documents d ON d.id = documents_fts.rowid
  WHERE documents_fts MATCH ?
    AND d.active = 1
    AND d.collection IN (${COLLECTION_PLACEHOLDERS})
  ORDER BY rank
  LIMIT 10
`);

const readStmt = db.prepare(`
  SELECT d.title, c.doc
  FROM documents d
  JOIN content c ON d.hash = c.hash
  WHERE d.collection = ? AND d.path = ? AND d.active = 1
`);

function createServer(user: string): McpServer {
  const server = new McpServer({ name: "vault", version: "1.0.0" });

  server.registerTool(
    "vault_search",
    {
      description:
        "Search the team knowledge vault using keywords (BM25). Returns up to 10 results with titles and snippets. Use vault_read to get the full document.",
      inputSchema: { query: z.string().describe("Search keywords") },
    },
    async ({ query }) => {
      const sanitized = sanitizeQuery(query);
      if (!sanitized) {
        return { content: [{ type: "text" as const, text: "Empty query after sanitization." }] };
      }

      const rows = searchStmt.all(sanitized, ...ALLOWED_COLLECTIONS) as {
        collection: string;
        path: string;
        title: string;
        snippet: string;
      }[];

      log(user, "vault_search", { query, results: rows.length });

      if (rows.length === 0) {
        return { content: [{ type: "text" as const, text: "No results found." }] };
      }

      const text = rows
        .map(
          (r, i) =>
            `${i + 1}. **${r.title}**\n   Path: \`${r.collection}/${r.path}\`\n   ${r.snippet.replace(/>>>/g, "**").replace(/<<</g, "**")}`,
        )
        .join("\n\n");

      return { content: [{ type: "text" as const, text }] };
    },
  );

  server.registerTool(
    "vault_read",
    {
      description:
        "Read the full content of a vault document. Use the path from vault_search results (format: collection/filepath).",
      inputSchema: {
        path: z.string().describe("Document path from search results, e.g. 'decisions/some-doc.md'"),
      },
    },
    async ({ path }) => {
      const slashIdx = path.indexOf("/");
      if (slashIdx === -1) {
        return {
          content: [{ type: "text" as const, text: "Invalid path format. Use: collection/filepath" }],
          isError: true,
        };
      }

      const collection = path.substring(0, slashIdx);
      const filePath = path.substring(slashIdx + 1);

      if (!ALLOWED_COLLECTIONS.includes(collection)) {
        log(user, "vault_read", { path, blocked: true });
        return {
          content: [{ type: "text" as const, text: "Access denied: collection not available." }],
          isError: true,
        };
      }

      const row = readStmt.get(collection, filePath) as { title: string; doc: string } | null;

      if (!row) {
        return {
          content: [{ type: "text" as const, text: `Document not found: ${path}` }],
          isError: true,
        };
      }

      log(user, "vault_read", { path });
      return { content: [{ type: "text" as const, text: row.doc }] };
    },
  );

  return server;
}

Bun.serve({
  port: PORT,
  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === "/health") {
      return new Response("ok");
    }

    // OAuth endpoints
    if (url.pathname === "/.well-known/oauth-protected-resource/mcp") {
      return oauth.handleProtectedResourceMetadata(BASE_URL);
    }
    if (url.pathname === "/.well-known/oauth-authorization-server") {
      return oauth.handleAuthServerMetadata(BASE_URL);
    }
    if (url.pathname === "/register" && req.method === "POST") {
      return oauth.handleRegister(req);
    }
    if (url.pathname === "/authorize" && req.method === "GET") {
      return oauth.handleAuthorize(req, BASE_URL);
    }
    if (url.pathname === "/oauth/google/callback" && req.method === "GET") {
      return oauth.handleGoogleCallback(req, BASE_URL);
    }
    if (url.pathname === "/token" && req.method === "POST") {
      return oauth.handleToken(req);
    }

    if (url.pathname === "/mcp") {
      // Try OAuth first, fall back to legacy bearer tokens
      let user = oauth.resolveUser(req.headers.get("authorization"));
      if (!user) {
        user = resolveLegacyUser(req.headers.get("authorization"));
      }
      if (!user) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), {
          status: 401,
          headers: {
            "Content-Type": "application/json",
            "WWW-Authenticate": `Bearer resource_metadata="${BASE_URL}/.well-known/oauth-protected-resource/mcp"`,
          },
        });
      }

      if (req.method === "POST") {
        const transport = new WebStandardStreamableHTTPServerTransport({
          sessionIdGenerator: undefined,
        });
        const server = createServer(user);
        await server.connect(transport);
        return transport.handleRequest(req);
      }

      if (req.method === "GET" || req.method === "DELETE") {
        return new Response("Stateless server — sessions not supported", { status: 405 });
      }

      return new Response("Method Not Allowed", { status: 405 });
    }

    return new Response("Not Found", { status: 404 });
  },
});

console.log(`vault-mcp listening on http://localhost:${PORT}`);
