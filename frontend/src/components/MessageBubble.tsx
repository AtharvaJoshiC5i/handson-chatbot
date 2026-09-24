import { useState } from "react";
import { ArrowUpRight, Check, Copy } from "lucide-react";

import type { ChatMessage } from "../types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
  onOptionSelect?: (message: string) => void;
  optionsDisabled?: boolean;
}

function formatTime(date: Date) {
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getStatusLabel(status: string) {
  switch (status) {
    case "VERIFIED":
      return "Verified";

    case "NOT_FOUND":
      return "Not found";

    case "UNSUPPORTED":
      return "Unsupported";

    case "API_ERROR":
      return "Error";

    default:
      return status;
  }
}

export function MessageBubble({
  message,
  onOptionSelect,
  optionsDisabled = false,
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [isCopied, setIsCopied] = useState(false);

  if (isUser) {
    return (
      <div className="group flex w-full justify-end">
        <div className="relative max-w-[78%] sm:max-w-[72%]">
          <button
            type="button"
            aria-label="Copy message"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(message.content);
                setIsCopied(true);
                window.setTimeout(() => setIsCopied(false), 1200);
              } catch {
                setIsCopied(false);
              }
            }}
            className="
              absolute -left-10 top-1/2 -translate-y-1/2
              flex h-7 w-7 items-center justify-center
              rounded-md border border-[#e2e2df] bg-white text-[#555552]
              opacity-0 shadow-sm transition-opacity duration-150
              pointer-events-none group-hover:pointer-events-auto group-hover:opacity-100
              group-focus-within:pointer-events-auto group-focus-within:opacity-100
              hover:border-[#c9c9c5] hover:text-[#292927]
            "
          >
            {isCopied ? (
              <Check size={14} strokeWidth={2} aria-hidden="true" />
            ) : (
              <Copy size={14} strokeWidth={2} aria-hidden="true" />
            )}
          </button>

          <div className="rounded-[18px] bg-[#f1f1ef] px-4 py-2.5 text-[13px] leading-[1.6] text-[#292927]">
            <p className="whitespace-pre-wrap wrap-break-word">
              {message.content}
            </p>
          </div>
          <div className="mt-1 text-[10px] leading-4 text-[#b0b0ac] opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100">
            {formatTime(message.createdAt)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="group w-full">
      {/* Assistant response */}
      <div className="text-[13px] leading-[1.7] text-[#292927]">
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
      </div>

      {/* Suggested actions */}
      {message.options && message.options.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {message.options.map((option) => (
            <button
              key={option.message}
              type="button"
              disabled={optionsDisabled}
              onClick={() => onOptionSelect?.(option.message)}
              className={[
                "group/option inline-flex min-h-8 items-center gap-1.5",
                "rounded-lg border border-[#e2e2df]",
                "bg-white px-2.5 py-1.5",
                "text-left text-[11px] font-medium text-[#555552]",
                "transition-colors duration-150",
                "hover:border-[#c9c9c5]",
                "hover:bg-[#f7f7f5]",
                "hover:text-[#292927]",
                "focus-visible:outline-none",
                "focus-visible:ring-2 focus-visible:ring-[#b8b8b3]",
                "focus-visible:ring-offset-2",
                "disabled:pointer-events-none",
                "disabled:opacity-40",
              ].join(" ")}
            >
              <span>{option.label}</span>

              <ArrowUpRight
                size={12}
                strokeWidth={1.8}
                className="shrink-0 text-[#9a9a96] transition-colors group-hover/option:text-[#555552]"
                aria-hidden="true"
              />
            </button>
          ))}
        </div>
      )}

      {/* Secondary metadata */}
      {(message.status || message.source) && (
        <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] leading-4 text-[#9a9a96]">
          {message.status && (
            <span className="font-medium text-[#777773]">
              {getStatusLabel(message.status)}
            </span>
          )}

          {message.status && message.source && (
            <span aria-hidden="true">·</span>
          )}

          {message.source && <span>{message.source}</span>}
        </div>
      )}

      {/* Timestamp — intentionally subtle */}
      <div className="mt-1 text-[10px] leading-4 text-[#b0b0ac] opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100">
        {formatTime(message.createdAt)}
      </div>
    </div>
  );
}
