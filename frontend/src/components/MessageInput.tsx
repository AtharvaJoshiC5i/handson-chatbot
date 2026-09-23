import { useState } from "react";

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function MessageInput({ onSend, disabled = false }: MessageInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || disabled) {
      return;
    }

    onSend(trimmedMessage);
    setMessage("");
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-[#dfe8e6] bg-white/80 p-4 sm:p-5">
      <div className="flex items-end gap-3">
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={2}
          maxLength={4000}
          placeholder="Ask about your plan, usage, bill, payments, tickets..."
          className="min-h-13.5 flex-1 resize-none rounded-xl border border-slate-300 bg-[#fbfcfb] px-4 py-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-teal-600 focus:ring-4 focus:ring-teal-100 disabled:cursor-not-allowed disabled:bg-slate-100"
        />

        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || message.trim().length === 0}
          className="rounded-xl bg-[#102d3c] px-5 py-3 text-sm font-semibold text-white shadow-[0_7px_16px_rgba(16,45,60,.18)] transition hover:-translate-y-0.5 hover:bg-[#17495a] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
        >
          {disabled ? "Sending..." : "Send"}
        </button>
      </div>

      <div className="mt-2 flex justify-between text-[11px] text-slate-400">
        <span>Enter to send · Shift + Enter for a new line</span>

        <span>{message.length}/4000</span>
      </div>
    </div>
  );
}
