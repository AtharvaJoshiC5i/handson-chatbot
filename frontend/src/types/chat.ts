export type ChatResponseStatus =
  | "VERIFIED"
  | "NOT_FOUND"
  | "AMBIGUOUS"
  | "UNSUPPORTED"
  | "DATABASE_ERROR"
  | "VALIDATION_ERROR"
  | "ACCESS_DENIED"
  | "API_ERROR";

export interface ChatResponse {
  message: string;
  status: ChatResponseStatus;
  source: string | null;
  options: ChatOption[];
}

export interface ChatOption {
  label: string;
  message: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: ChatResponseStatus;
  source?: string | null;
  options?: ChatOption[];
  createdAt: Date;
}
