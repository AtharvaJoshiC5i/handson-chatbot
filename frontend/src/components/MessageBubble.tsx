import { useState } from "react";

import { Check, Copy, ArrowUpRight } from "lucide-react";

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
  const [copied, setCopied] = useState(false);

  const isUser = message.role === "user";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);

      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 1600);
    } catch {
      setCopied(false);
    }
  };

  if (isUser) {
    return (
      <div className="group flex w-full justify-end">
        <div className="max-w-[78%] sm:max-w-[72%]">
          {/* User message */}
          <div className="rounded-[18px] bg-[#f1f1ef] px-4 py-2.5 text-[13px] leading-[1.6] text-[#292927]">
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </div>

          {/* User message actions */}
          <div
            className={[
              "mt-1.5 flex h-6 items-center justify-end gap-2",
              "opacity-0 transition-opacity duration-150",
              "group-hover:opacity-100",
              "group-focus-within:opacity-100",
            ].join(" ")}
          >
            <span className="text-[10px] tabular-nums text-[#aaa9a5]">
              {formatTime(message.createdAt)}
            </span>

            <button
              type="button"
              onClick={handleCopy}
              aria-label={copied ? "Message copied" : "Copy message"}
              title={copied ? "Copied" : "Copy"}
              className={[
                "flex h-6 w-6 items-center justify-center rounded-md",
                "text-[#999995]",
                "transition-colors duration-150",
                "hover:bg-[#f1f1ef]",
                "hover:text-[#4f4f4b]",
                "focus-visible:outline-none",
                "focus-visible:ring-2",
                "focus-visible:ring-[#b8b8b3]",
              ].join(" ")}
            >
              {copied ? (
                <Check size={13} strokeWidth={2} aria-hidden="true" />
              ) : (
                <Copy size={13} strokeWidth={1.8} aria-hidden="true" />
              )}
            </button>
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
                "focus-visible:ring-2",
                "focus-visible:ring-[#b8b8b3]",
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

      {/* Source metadata */}
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

      {/* Assistant actions */}
      <div
        className={[
          "mt-1.5 flex h-6 items-center gap-2",
          "opacity-0 transition-opacity duration-150",
          "group-hover:opacity-100",
          "group-focus-within:opacity-100",
        ].join(" ")}
      >
        <span className="text-[10px] tabular-nums text-[#aaa9a5]">
          {formatTime(message.createdAt)}
        </span>

        <button
          type="button"
          onClick={handleCopy}
          aria-label={copied ? "Response copied" : "Copy response"}
          title={copied ? "Copied" : "Copy"}
          className={[
            "flex h-6 w-6 items-center justify-center rounded-md",
            "text-[#999995]",
            "transition-colors duration-150",
            "hover:bg-[#f1f1ef]",
            "hover:text-[#4f4f4b]",
            "focus-visible:outline-none",
            "focus-visible:ring-2",
            "focus-visible:ring-[#b8b8b3]",
          ].join(" ")}
        >
          {copied ? (
            <Check size={13} strokeWidth={2} aria-hidden="true" />
          ) : (
            <Copy size={13} strokeWidth={1.8} aria-hidden="true" />
          )}
        </button>
      </div>
    </div>
  );
}
