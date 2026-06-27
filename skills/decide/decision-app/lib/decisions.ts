export interface Option {
  label: string;
  description: string;
}

export interface Question {
  id: string;
  question: string;
  header: string;
  options: Option[];
}

export interface Decision {
  id: string;
  title: string;
  description: string;
  source?: string;
  status: "active" | "closed";
  team: string[];
  context?: string;
  questions: Question[];
  markdownContent?: string;
  createdAt?: string;
  createdBy?: string;
}

export const DEFAULT_TEAM: readonly string[] = (
  process.env.DECIDE_TEAM
    ? process.env.DECIDE_TEAM.split(",").map(s => s.trim())
    : ["Alice", "Bob", "Carol"]
) as readonly string[];
