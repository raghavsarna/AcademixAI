// Shapes returned by the FastAPI backend (see app/schemas.py).

export const DEPTHS = ["plain", "student", "expert"] as const;
export type Depth = (typeof DEPTHS)[number];

export const DEPTH_LABELS: Record<Depth, string> = {
  plain: "Plain",
  student: "Student",
  expert: "Expert",
};

export const CHANGE_TYPE_LABELS: Record<string, string> = {
  "new-method": "New method",
  "new-result": "New result",
  benchmark: "New benchmark",
  dataset: "New dataset",
  analysis: "Analysis",
  challenge: "Challenges prior work",
  tool: "Tool or system",
  survey: "Survey",
};

export type BuildsOn = { work: string; relation: string };

export type PaperSummary = {
  id: string;
  title: string;
  authors: string[];
  source: string | null;
  doi: string | null;
  origin: "arxiv" | "upload";
  created_at: string;
};

export type PaperCard = PaperSummary & {
  arxiv_id: string | null;
  source_url: string | null;
  categories: string[];
  short_name: string | null;
  change_type: string | null;
  what_changed: string | null;
  why_it_matters: string | null;
  builds_on: BuildsOn[];
};

export type PaperDetail = PaperCard & {
  publication_date: string | null;
  keywords: string[];
  abstract: string | null;
  explanations: Partial<Record<Depth, string>>;
  main_findings: string | null;
  methodology: string | null;
};

export type MyPaper = PaperSummary & {
  uploaded_at: string;
  filename: string;
  what_changed: string | null;
};

export type Theme = { name: string; summary: string; papers: string[] };

export type EditionSummary = {
  id: number;
  edition_date: string;
  headline: string;
  overview: string;
  papers_scanned: number;
  entry_count: number;
};

export type EditionDetail = Omit<EditionSummary, "entry_count"> & {
  themes: Theme[];
  entries: { rank: number; paper: PaperCard }[];
  previous_date: string | null;
  next_date: string | null;
};

export type User = { id: number; email: string; username: string; created_at: string };

export type UploadJobStatus = "queued" | "reading" | "analysing" | "ready" | "failed";

/** An upload being explained in the background. Poll it until it is ready or failed. */
export type UploadJob = {
  id: string;
  filename: string;
  status: UploadJobStatus;
  error: string | null;
  paper_id: string | null;
  paper_title: string | null;
  url: string | null;
  created_at: string;
  updated_at: string;
};

export const ACTIVE_JOB: UploadJobStatus[] = ["queued", "reading", "analysing"];

/** A passage of the paper that an answer cites as [number]. */
export type ChatSource = { number: number; section: string | null; page: number | null; text: string };

export type ChatAnswer = { reply: string; sources: ChatSource[] };
