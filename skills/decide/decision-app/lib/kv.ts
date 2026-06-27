import { Redis } from "@upstash/redis";

export interface VoteResponse {
  name: string;
  decisionId: string;
  answers: Record<string, { selected: string; reasoning: string }>;
  submittedAt: string;
}

// Use Upstash Redis if env vars are set, otherwise fall back to in-memory store
let redis: Redis | null = null;

function getRedis(): Redis | null {
  if (redis) return redis;
  if (
    process.env.UPSTASH_REDIS_REST_URL &&
    process.env.UPSTASH_REDIS_REST_TOKEN
  ) {
    redis = new Redis({
      url: process.env.UPSTASH_REDIS_REST_URL,
      token: process.env.UPSTASH_REDIS_REST_TOKEN,
    });
    return redis;
  }
  return null;
}

// In-memory fallback for local development
const memoryStore = new Map<string, string>();

function sanitizeKeyPart(s: string): string {
  return s.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 100);
}

export async function saveResponse(response: VoteResponse): Promise<void> {
  const key = `response:${sanitizeKeyPart(response.decisionId)}:${sanitizeKeyPart(response.name)}`;
  const value = JSON.stringify(response);
  const r = getRedis();
  if (r) {
    await r.set(key, value);
  } else {
    memoryStore.set(key, value);
  }
}

export async function getResponse(
  decisionId: string,
  name: string
): Promise<VoteResponse | null> {
  const key = `response:${sanitizeKeyPart(decisionId)}:${sanitizeKeyPart(name)}`;
  const r = getRedis();
  if (r) {
    const val = await r.get<string>(key);
    return val ? (typeof val === "string" ? JSON.parse(val) : val as unknown as VoteResponse) : null;
  }
  const val = memoryStore.get(key);
  return val ? JSON.parse(val) : null;
}

export async function getAllResponses(decisionId?: string): Promise<VoteResponse[]> {
  const pattern = decisionId ? `response:${sanitizeKeyPart(decisionId)}:*` : "response:*";
  const r = getRedis();
  if (r) {
    const keys = await r.keys(pattern);
    if (keys.length === 0) return [];
    const results: VoteResponse[] = [];
    for (const key of keys) {
      const val = await r.get<string>(key);
      if (val) {
        results.push(typeof val === "string" ? JSON.parse(val) : val as unknown as VoteResponse);
      }
    }
    return results;
  }
  // In-memory fallback
  const results: VoteResponse[] = [];
  const prefix = decisionId ? `response:${sanitizeKeyPart(decisionId)}:` : "response:";
  for (const [key, val] of memoryStore) {
    if (key.startsWith(prefix)) {
      results.push(JSON.parse(val));
    }
  }
  return results;
}
