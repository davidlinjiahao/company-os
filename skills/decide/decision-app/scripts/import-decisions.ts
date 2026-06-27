#!/usr/bin/env npx tsx

import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";
import { stringify } from "yaml";

const OBSIDIAN_DECISIONS_PATH = process.env.OBSIDIAN_DECISIONS_PATH
  || `${process.env.HOME}/Documents/ObsidianVault/Decisions`;
const OUTPUT_PATH = path.join(process.cwd(), "decisions");

const client = new Anthropic();

interface DecisionYAML {
  id: string;
  title: string;
  description: string;
  source: string;
  status: "active" | "closed";
  team: string[];
  context: string;
  questions: {
    id: string;
    header: string;
    question: string;
    options: { label: string; description: string }[];
  }[];
}

async function extractDecisionFromMarkdown(
  filePath: string,
  content: string
): Promise<DecisionYAML | null> {
  const fileName = path.basename(filePath, ".md");

  // Skip non-decision files
  const skipPatterns = ["Transcripts", "PRD", "Meeting", "Contract", "Archives"];
  if (skipPatterns.some(p => filePath.includes(p))) {
    console.log(`  Skipping: ${fileName} (not a decision doc)`);
    return null;
  }

  console.log(`  Processing: ${fileName}`);

  const prompt = `Analyze this decision document and extract structured voting questions.

Document: ${fileName}
---
${content.slice(0, 8000)}
---

Extract the key decision points that a team should vote on. For each decision point, create a question with 2-4 options.

Respond with ONLY valid JSON (no markdown, no explanation):
{
  "title": "Decision: [short title]",
  "description": "[1-2 sentence summary of what's being decided]",
  "status": "active or closed (closed if decision is already made)",
  "context": "[2-3 paragraph summary of the key context and tradeoffs]",
  "questions": [
    {
      "id": "q1",
      "header": "[short category like 'Approach', 'Timeline', 'Budget']",
      "question": "[the question to vote on]",
      "options": [
        {"label": "[option name]", "description": "[1 sentence explaining this option]"},
        {"label": "[option name]", "description": "[1 sentence explaining this option]"}
      ]
    }
  ]
}

Rules:
- Extract 1-4 meaningful decision questions
- If the doc already has a clear recommendation/decision made, set status to "closed"
- Each question should have 2-4 options
- Options should be mutually exclusive
- If the document isn't actually a decision (just notes/PRD/meeting notes), return {"skip": true}`;

  try {
    const message = await client.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 2000,
      messages: [{ role: "user", content: prompt }],
    });

    const responseText = message.content[0].type === "text" ? message.content[0].text : "";

    // Parse JSON from response
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      console.log(`    Failed to extract JSON`);
      return null;
    }

    const parsed = JSON.parse(jsonMatch[0]);

    if (parsed.skip) {
      console.log(`    Skipped (not a decision doc)`);
      return null;
    }

    // Generate ID from filename
    const id = fileName
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 50);

    return {
      id,
      title: parsed.title,
      description: parsed.description,
      source: fileName,
      status: parsed.status || "active",
      team: (process.env.DECIDE_TEAM || "Alice,Bob,Carol").split(",").map(s => s.trim()),
      context: parsed.context || "",
      questions: parsed.questions || [],
    };
  } catch (error) {
    console.log(`    Error processing: ${error}`);
    return null;
  }
}

async function findDecisionFiles(dir: string): Promise<string[]> {
  const files: string[] = [];

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      // Skip Archives
      if (entry.name === "Archives") continue;
      files.push(...await findDecisionFiles(fullPath));
    } else if (entry.name.endsWith(".md") && !entry.name.startsWith(".")) {
      files.push(fullPath);
    }
  }

  return files;
}

async function main() {
  console.log("Importing decisions from Obsidian...\n");
  console.log(`Source: ${OBSIDIAN_DECISIONS_PATH}`);
  console.log(`Output: ${OUTPUT_PATH}\n`);

  // Ensure output directory exists
  if (!fs.existsSync(OUTPUT_PATH)) {
    fs.mkdirSync(OUTPUT_PATH, { recursive: true });
  }

  // Find all markdown files
  const files = await findDecisionFiles(OBSIDIAN_DECISIONS_PATH);
  console.log(`Found ${files.length} markdown files\n`);

  const decisions: DecisionYAML[] = [];

  for (const file of files) {
    const content = fs.readFileSync(file, "utf-8");

    // Skip very short files or files without decision-like content
    if (content.length < 500) {
      console.log(`  Skipping: ${path.basename(file)} (too short)`);
      continue;
    }

    const decision = await extractDecisionFromMarkdown(file, content);
    if (decision && decision.questions.length > 0) {
      decisions.push(decision);
    }

    // Rate limiting
    await new Promise(r => setTimeout(r, 500));
  }

  console.log(`\nExtracted ${decisions.length} decisions\n`);

  // Write YAML files
  for (const decision of decisions) {
    const yamlPath = path.join(OUTPUT_PATH, `${decision.id}.yaml`);
    const yamlContent = stringify(decision);
    fs.writeFileSync(yamlPath, yamlContent);
    console.log(`Written: ${decision.id}.yaml (${decision.questions.length} questions)`);
  }

  console.log("\nDone!");
}

main().catch(console.error);
