import { NextResponse } from "next/server";
import { extractQuestionsFromMarkdown } from "@/lib/extract-questions";
import { saveDecision, getDecision } from "@/lib/decisions-store";
import type { Decision } from "@/lib/decisions";

// Allow up to 60 seconds for Claude extraction
export const maxDuration = 60;

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;
    const createdBy = (formData.get("createdBy") as string) || "admin";

    if (!file || !file.name.endsWith(".md")) {
      return NextResponse.json(
        { error: "Please upload a .md file" },
        { status: 400 }
      );
    }

    const content = await file.text();

    if (content.length < 100) {
      return NextResponse.json(
        { error: "File is too short to be a decision document" },
        { status: 400 }
      );
    }

    // Extract questions using Claude
    const extracted = await extractQuestionsFromMarkdown(file.name, content);

    // Check if decision already exists
    const existing = await getDecision(extracted.id);
    if (existing) {
      return NextResponse.json(
        { error: `A decision with ID "${extracted.id}" already exists. Delete it first or rename your file.`, existingId: extracted.id },
        { status: 409 }
      );
    }

    // Build full decision object
    const decision: Decision = {
      ...extracted,
      markdownContent: content,
      createdAt: new Date().toISOString(),
      createdBy,
    };

    await saveDecision(decision);

    return NextResponse.json({
      decision: {
        id: decision.id,
        title: decision.title,
        description: decision.description,
        questionCount: decision.questions.length,
        questions: decision.questions,
      },
      shareUrl: `/vote/${decision.id}`,
    });
  } catch (error) {
    console.error("Upload API error:", error);

    // Surface the actual error message
    const message =
      error instanceof Error ? error.message : "Unknown error occurred";

    // Classify the error for the user
    let userMessage: string;
    if (message.includes("Could not resolve authentication")) {
      userMessage = "Anthropic API key is not configured. Check ANTHROPIC_API_KEY env var.";
    } else if (message.includes("401") || message.includes("authentication")) {
      userMessage = "Anthropic API key is invalid. Check ANTHROPIC_API_KEY env var.";
    } else if (message.includes("rate") || message.includes("429")) {
      userMessage = "Rate limited by Anthropic API. Wait a minute and try again.";
    } else if (message.includes("timeout") || message.includes("ETIMEDOUT")) {
      userMessage = "Request timed out. The document may be too large. Try again.";
    } else if (message.includes("Redis") || message.includes("UPSTASH")) {
      userMessage = "Failed to save to database. Check Redis configuration.";
    } else {
      userMessage = "An unexpected error occurred. Please try again.";
    }

    return NextResponse.json(
      { error: userMessage },
      { status: 500 }
    );
  }
}
