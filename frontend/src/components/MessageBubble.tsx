import type { ChatMessage } from "../types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ${
          isUser
            ? "rounded-br-md bg-[#102d3c] text-white shadow-[0_8px_18px_rgba(16,45,60,.12)]"
            : "rounded-bl-md border border-[#dce7e4] bg-white text-slate-800 shadow-[0_6px_16px_rgba(49,78,82,.06)]"
        }`}
      >
        <div className="whitespace-pre-wrap wrap-break-word text-sm leading-6">
          {message.content}
        </div>

        {!isUser && message.status && (
          <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-2">
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                message.status === "VERIFIED"
                  ? "bg-emerald-100 text-emerald-700"
                  : message.status === "NOT_FOUND"
                    ? "bg-amber-100 text-amber-700"
                    : message.status === "UNSUPPORTED"
                      ? "bg-slate-100 text-slate-600"
                      : "bg-red-100 text-red-700"
              }`}
            >
              {message.status}
            </span>

            {message.source && (
              <span className="text-[10px] text-slate-400">
                Source: {message.source}
              </span>
            )}
          </div>
        )}

        <div
          className={`mt-1 text-[10px] ${
            isUser ? "text-slate-300" : "text-slate-400"
          }`}
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
