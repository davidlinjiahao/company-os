import { NextResponse } from "next/server";
import JSZip from "jszip";
import { getAllResponses } from "@/lib/kv";
import { getAllDecisions, getDecision, getSynthesis } from "@/lib/decisions-store";
import {
  generatePersonMarkdown,
  generateSummaryMarkdown,
  generateFullReportMarkdown,
} from "@/lib/export";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const decisionId = searchParams.get("decisionId");
    const format = searchParams.get("format");

    const decisions = decisionId
      ? await (async () => { const d = await getDecision(decisionId); return d ? [d] : []; })()
      : await getAllDecisions();

    if (decisions.length === 0) {
      return NextResponse.json(
        { error: "Decision not found" },
        { status: 404 }
      );
    }

    const responses = await getAllResponses(decisionId ?? undefined);

    if (responses.length === 0) {
      return NextResponse.json(
        { error: "No responses to export" },
        { status: 404 }
      );
    }

    // Single .md report format
    if (format === "single" && decisionId && decisions.length === 1) {
      const synthesis = await getSynthesis(decisionId);
      const md = generateFullReportMarkdown(decisions[0], responses, synthesis ?? undefined);
      const filename = `decision-${decisionId}-report.md`;

      return new NextResponse(md, {
        headers: {
          "Content-Type": "text/markdown; charset=utf-8",
          "Content-Disposition": `attachment; filename="${filename}"`,
        },
      });
    }

    // Default: ZIP format
    const zip = new JSZip();

    // Individual response files
    for (const response of responses) {
      const md = generatePersonMarkdown(decisions, response);
      zip.file(`${response.name}-responses.md`, md);
    }

    // Summary file
    const summary = generateSummaryMarkdown(decisions, responses);
    zip.file("decision-summary.md", summary);

    const zipBuffer = await zip.generateAsync({ type: "arraybuffer" });

    const filename = decisionId
      ? `decision-${decisionId}-votes.zip`
      : "decision-votes.zip";

    return new NextResponse(zipBuffer, {
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    });
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
