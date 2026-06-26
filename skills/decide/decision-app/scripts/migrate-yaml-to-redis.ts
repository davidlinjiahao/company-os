#!/usr/bin/env npx tsx

/**
 * One-time migration: reads all YAML decision files from decisions/
 * and saves each to Redis via decisions-store.
 *
 * Run: UPSTASH_REDIS_REST_URL=... UPSTASH_REDIS_REST_TOKEN=... npx tsx scripts/migrate-yaml-to-redis.ts
 */

import fs from "fs";
import path from "path";
import { parse } from "yaml";
import type { Decision } from "../lib/decisions";

// Inline Redis logic since we can't use the app's module resolution (@/) in scripts
import { Redis } from "@upstash/redis";

const DECISION_INDEX_KEY = "decision:index";

function decisionKey(id: string): string {
  return `decision:${id}`;
}

async function main() {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;

  if (!url || !token) {
    console.error("Error: UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be set.");
    process.exit(1);
  }

  const redis = new Redis({ url, token });
  const decisionsDir = path.join(process.cwd(), "decisions");

  if (!fs.existsSync(decisionsDir)) {
    console.error(`Error: decisions/ directory not found at ${decisionsDir}`);
    process.exit(1);
  }

  const files = fs.readdirSync(decisionsDir).filter((f) => f.endsWith(".yaml"));
  console.log(`Found ${files.length} YAML files in decisions/\n`);

  let migrated = 0;

  for (const file of files) {
    const content = fs.readFileSync(path.join(decisionsDir, file), "utf-8");
    const decision = parse(content) as Decision;

    // Add migration metadata
    decision.createdAt = decision.createdAt || new Date().toISOString();
    decision.createdBy = decision.createdBy || "migration";

    const key = decisionKey(decision.id);
    await redis.set(key, JSON.stringify(decision));
    await redis.sadd(DECISION_INDEX_KEY, decision.id);

    console.log(`  Migrated: ${decision.id} (${decision.title})`);
    migrated++;
  }

  console.log(`\nDone! Migrated ${migrated} decisions to Redis.`);

  // Verify
  const ids = await redis.smembers(DECISION_INDEX_KEY);
  console.log(`\nVerification: ${ids.length} decisions in Redis index:`);
  for (const id of ids) {
    const val = await redis.get<string>(decisionKey(id));
    if (val) {
      const d = typeof val === "string" ? JSON.parse(val) : val;
      console.log(`  - ${id}: ${(d as Decision).title}`);
    } else {
      console.log(`  - ${id}: MISSING DATA`);
    }
  }
}

main().catch(console.error);
