import type { ChatMessage } from "../types/chat";

import { ArrowRight, Bot } from "lucide-react";

interface MessageBubbleProps {
  message: ChatMessage;
  onOptionSelect?: (message: string) => void;
  optionsDisabled?: boolean;
}

export function MessageBubble({
  message,
  onOptionSelect,
  optionsDisabled = false,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex w-full items-start gap-3 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="grid size-8 shrink-0 place-items-center rounded-xl bg-[#123442] text-sm text-white shadow-sm shadow-[#123442]/20">
          <Bot size={16} strokeWidth={2.2} aria-hidden="true" />
        </div>
      )}
      <div
        className={`max-w-[88%] ${isUser ? "rounded-2xl rounded-br-md bg-[#173b4a] px-4 py-3 text-white shadow-lg shadow-[#173b4a]/10" : "pt-1 text-[#294551]"}`}
      >
        <div className="whitespace-pre-wrap wrap-break-word text-sm leading-7">
          {message.content}
        </div>

        {!isUser && message.options && message.options.length > 0 && (
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {message.options.map((option) => (
              <button
                key={option.message}
                type="button"
                disabled={optionsDisabled}
                onClick={() => onOptionSelect?.(option.message)}
                className="group flex min-h-10 items-center justify-between gap-3 rounded-xl border border-[#b9d8d1] bg-white px-3 py-2 text-left text-xs font-bold text-[#24545a] shadow-sm transition hover:border-[#42a99d] hover:bg-[#f1faf7] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span>{option.label}</span>
                <ArrowRight
                  size={15}
                  className="shrink-0 text-[#138d80] transition-transform group-hover:translate-x-0.5"
                  aria-hidden="true"
                />
              </button>
            ))}
          </div>
        )}

        {!isUser && message.status && (
          <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-[#e7efed] pt-2">
            <span
              className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.06em] ${
                message.status === "VERIFIED"
                  ? "bg-[#e4f5ef] text-[#147866]"
                  : message.status === "NOT_FOUND"
                    ? "bg-[#fff5dc] text-[#9d6b18]"
                    : message.status === "UNSUPPORTED"
                      ? "bg-[#edf1f1] text-[#607278]"
                      : "bg-[#fff0ed] text-[#a2493d]"
              }`}
            >
              {message.status}
            </span>

            {message.source && (
              <span className="text-[10px] text-[#9aa8aa]">
                Source: {message.source}
              </span>
            )}
          </div>
        )}

        <div
          className={`mt-1 text-[10px] ${isUser ? "text-[#a9c0c7]" : "text-[#a1afb0]"}`}
        >
          {message.createdAt.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>
    </div>
  );
}
