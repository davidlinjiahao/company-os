import { Redis } from "@upstash/redis";
import type { Decision } from "./decisions";

let redis: Redis | null = null;

function getRedis(): Redis | null {
  if (redis) return redis;
  if (
    process.env.UPSTASH_REDIS_REST_URL &&
    process.env.UPSTASH_REDIS_REST_TOKEN
  ) {
    redis = new Redis({
      url: process.env.UPSTASH_REDIS_REST_URL.trim(),
      token: process.env.UPSTASH_REDIS_REST_TOKEN.trim(),
    });
    return redis;
  }
  return null;
}

const memoryStore = new Map<string, string>();

const DECISION_INDEX_KEY = "decision:index";

function sanitizeKeyPart(s: string): string {
  return s.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 100);
}

function decisionKey(id: string): string {
  return `decision:${sanitizeKeyPart(id)}`;
}

function synthesisKey(decisionId: string): string {
  return `synthesis:${sanitizeKeyPart(decisionId)}`;
}

export async function saveDecision(decision: Decision): Promise<void> {
  const key = decisionKey(decision.id);
  const value = JSON.stringify(decision);
  const r = getRedis();
  if (r) {
    await r.set(key, value);
    await r.sadd(DECISION_INDEX_KEY, decision.id);
  } else {
    memoryStore.set(key, value);
    const indexRaw = memoryStore.get(DECISION_INDEX_KEY);
    const index: string[] = indexRaw ? JSON.parse(indexRaw) : [];
    if (!index.includes(decision.id)) {
      index.push(decision.id);
      memoryStore.set(DECISION_INDEX_KEY, JSON.stringify(index));
    }
  }
}

export async function getDecision(id: string): Promise<Decision | null> {
  const key = decisionKey(id);
  const r = getRedis();
  if (r) {
    const val = await r.get<string>(key);
    if (!val) return null;
    return typeof val === "string" ? JSON.parse(val) : (val as unknown as Decision);
  }
  const val = memoryStore.get(key);
  return val ? JSON.parse(val) : null;
}

export async function getAllDecisions(): Promise<Decision[]> {
  const r = getRedis();
  if (r) {
    const ids = await r.smembers(DECISION_INDEX_KEY);
    if (ids.length === 0) return [];
    const pipeline = r.pipeline();
    for (const id of ids) {
      pipeline.get(decisionKey(id));
    }
    const results = await pipeline.exec();
    return results
      .filter((val): val is string | Decision => val !== null)
      .map((val) =>
        typeof val === "string" ? JSON.parse(val) : (val as Decision)
      );
  }
  const indexRaw = memoryStore.get(DECISION_INDEX_KEY);
  const index: string[] = indexRaw ? JSON.parse(indexRaw) : [];
  const decisions: Decision[] = [];
  for (const id of index) {
    const val = memoryStore.get(decisionKey(id));
    if (val) decisions.push(JSON.parse(val));
  }
  return decisions;
}

export async function deleteDecision(id: string): Promise<void> {
  const r = getRedis();
  if (r) {
    await r.del(decisionKey(id));
    await r.srem(DECISION_INDEX_KEY, id);
  } else {
    memoryStore.delete(decisionKey(id));
    const indexRaw = memoryStore.get(DECISION_INDEX_KEY);
    const index: string[] = indexRaw ? JSON.parse(indexRaw) : [];
    const filtered = index.filter((i) => i !== id);
    memoryStore.set(DECISION_INDEX_KEY, JSON.stringify(filtered));
  }
}

export async function saveSynthesis(
  decisionId: string,
  text: string
): Promise<void> {
  const key = synthesisKey(decisionId);
  const r = getRedis();
  if (r) {
    await r.set(key, text);
  } else {
    memoryStore.set(key, text);
  }
}

export async function deleteSynthesis(
  decisionId: string
): Promise<void> {
  const key = synthesisKey(decisionId);
  const r = getRedis();
  if (r) {
    await r.del(key);
  } else {
    memoryStore.delete(key);
  }
}

export async function getSynthesis(
  decisionId: string
): Promise<string | null> {
  const key = synthesisKey(decisionId);
  const r = getRedis();
  if (r) {
    const val = await r.get<string>(key);
    return val ?? null;
  }
  return memoryStore.get(key) ?? null;
}
