import type { ChatMessage } from "../types/chat";

import { Bot } from "lucide-react";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
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
