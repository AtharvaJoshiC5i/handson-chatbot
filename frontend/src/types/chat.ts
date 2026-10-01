export type ChatResponseStatus =
  | "VERIFIED"
  | "NOT_FOUND"
  | "AMBIGUOUS"
  | "UNSUPPORTED"
  | "DATABASE_ERROR"
  | "VALIDATION_ERROR"
  | "ACCESS_DENIED"
  | "API_ERROR";

export interface ChatOption {
  label: string;
  message: string;
}

/* ============================================================
 * Structured presentation types
 * ============================================================
 */

export interface KeyValueItem {
  label: string;
  value: string;
}

export interface KeyValuePresentation {
  type: "key_value";
  title?: string | null;
  items: KeyValueItem[];
}

export interface ComparisonColumn {
  key: string;
  label: string;
}

export interface ComparisonRow {
  label: string;
  values: Record<string, string>;
}

export interface ComparisonPresentation {
  type: "comparison";
  title?: string | null;
  columns: ComparisonColumn[];
  rows: ComparisonRow[];
}

export interface ListItem {
  label: string;
  value: string;
  detail?: string | null;
}

export interface ListPresentation {
  type: "list";
  title?: string | null;
  items: ListItem[];
}

export interface TableColumn {
  key: string;
  label: string;
  align?: "left" | "right";
}

export interface TablePresentation {
  type: "table";
  title?: string | null;
  columns: TableColumn[];
  rows: Record<string, string>[];
}

export interface TimeSeriesPoint {
  period: string;
  value: number;
  detail?: string | null;
}

export interface TimeSeriesPresentation {
  type: "time_series";
  title?: string | null;
  chart_type: "line" | "bar";
  unit: string;
  value_format: "number" | "inr";
  points: TimeSeriesPoint[];
}

export interface SummarySection {
  label: string;
  primary: string;
  secondary?: string | null;
}

export interface SummaryPresentation {
  type: "summary";
  title?: string | null;
  sections: SummarySection[];
}

export interface Customer360Table {
  title: string;
  columns: TableColumn[];
  rows: Record<string, string>[];
}

export interface Customer360Presentation {
  type: "customer_360";
  title?: string | null;
  sections: SummarySection[];
  tables: Customer360Table[];
}

export type ChatPresentation =
  | KeyValuePresentation
  | ComparisonPresentation
  | ListPresentation
  | TablePresentation
  | TimeSeriesPresentation
  | SummaryPresentation
  | Customer360Presentation;

/* ============================================================
 * API contract
 * ============================================================
 */

export interface ChatResponse {
  message: string;
  status: ChatResponseStatus;
  source: string | null;
  presentation?: ChatPresentation | null;
  options: ChatOption[];
}

/* ============================================================
 * Local conversation model
 * ============================================================
 */

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: ChatResponseStatus;
  source?: string | null;
  presentation?: ChatPresentation | null;
  options?: ChatOption[];
  createdAt: Date;
  isStreaming?: boolean;
}