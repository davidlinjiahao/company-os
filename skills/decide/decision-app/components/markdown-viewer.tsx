"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownViewerProps {
  content: string;
  defaultExpanded?: boolean;
}

/**
 * Strip the "Decision Questions for the Team" section and everything after it,
 * since those questions are rendered as interactive voting cards below.
 */
function stripQuestionsSection(md: string): string {
  // Match common heading variants for the questions section
  const patterns = [
    /^#{1,3}\s+Decision Questions for the Team.*$/im,
    /^#{1,3}\s+Decision Questions.*$/im,
    /^#{1,3}\s+Questions for the Team.*$/im,
  ];
  for (const pattern of patterns) {
    const match = md.search(pattern);
    if (match !== -1) {
      return md.slice(0, match).trimEnd();
    }
  }
  return md;
}

export function MarkdownViewer({
  content,
  defaultExpanded = true,
}: MarkdownViewerProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const displayContent = stripQuestionsSection(content);

  return (
    <div className="rounded-xl border border-zinc-800/80 bg-[#16213e]/40 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-3 text-left cursor-pointer hover:bg-zinc-800/20 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-indigo-400 text-xs">doc</span>
          <span className="text-sm font-medium text-zinc-300">
            Decision Context
          </span>
        </div>
        <span className="text-xs text-zinc-500">
          {expanded ? "Collapse" : "Expand"}
        </span>
      </button>

      {expanded && (
        <div className="px-5 pb-5 border-t border-zinc-800/50">
          <div className="mt-4 prose prose-invert prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => (
                  <h1 className="text-lg font-bold text-zinc-100 mt-6 mb-3 first:mt-0">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-base font-semibold text-zinc-200 mt-5 mb-2">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-semibold text-zinc-300 mt-4 mb-1.5">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="text-sm text-zinc-300 leading-relaxed mb-3">
                    {children}
                  </p>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {children}
                  </a>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside text-sm text-zinc-300 space-y-1 mb-3 ml-2">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside text-sm text-zinc-300 space-y-1 mb-3 ml-2">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="text-sm text-zinc-300">{children}</li>
                ),
                strong: ({ children }) => (
                  <strong className="text-zinc-200 font-semibold">
                    {children}
                  </strong>
                ),
                em: ({ children }) => (
                  <em className="text-zinc-300 italic">{children}</em>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-indigo-500/40 pl-4 my-3 text-sm text-zinc-300 italic">
                    {children}
                  </blockquote>
                ),
                code: ({ children, className }) => {
                  const isBlock = className?.includes("language-");
                  if (isBlock) {
                    return (
                      <code className="block rounded-lg bg-zinc-900/50 border border-zinc-800/50 p-3 text-xs text-zinc-300 font-mono overflow-x-auto my-3">
                        {children}
                      </code>
                    );
                  }
                  return (
                    <code className="rounded bg-zinc-800/50 px-1.5 py-0.5 text-xs text-indigo-300 font-mono">
                      {children}
                    </code>
                  );
                },
                pre: ({ children }) => (
                  <pre className="my-3">{children}</pre>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto my-3">
                    <table className="w-full text-sm border-collapse">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="border-b border-zinc-700">{children}</thead>
                ),
                th: ({ children }) => (
                  <th className="px-3 py-2 text-left text-xs font-medium text-zinc-300 bg-zinc-800/30">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-3 py-2 text-xs text-zinc-300 border-b border-zinc-800/30">
                    {children}
                  </td>
                ),
                hr: () => <hr className="my-4 border-zinc-800/50" />,
              }}
            >
              {displayContent}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
