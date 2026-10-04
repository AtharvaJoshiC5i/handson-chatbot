import type { ChatResponseStatus } from "../types/chat";

const STATUS_COPY: Partial<
  Record<ChatResponseStatus, { label: string; tone: string }>
> = {
  VERIFIED: {
    label: "From your account records",
    tone: "text-[#3d6b55]",
  },
  AMBIGUOUS: {
    label: "Answer may need clarification",
    tone: "text-[#8a5c1a]",
  },
  NOT_FOUND: {
    label: "No matching account record",
    tone: "text-[#8b5a54]",
  },
  UNSUPPORTED: {
    label: "Not available for this account",
    tone: "text-[#7d8b81]",
  },
};

interface AnswerTrustFooterProps {
  status?: ChatResponseStatus;
  source?: string | null;
}

export function AnswerTrustFooter({
  status,
  source,
}: AnswerTrustFooterProps) {
  if (!status) {
    return null;
  }

  const copy = STATUS_COPY[status];

  if (!copy) {
    return null;
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-[#edf1ed] pt-2 text-[10px]">
      <span className={`font-medium ${copy.tone}`}>
        {copy.label}
      </span>
      {source && status === "VERIFIED" && (
        <span
          className="truncate text-[#96a198]"
          title={source}
        >
          · {source.replace(/^sqlite\./, "")}
        </span>
      )}
    </div>
  );
}
