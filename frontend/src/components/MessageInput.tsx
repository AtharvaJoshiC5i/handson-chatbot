import { useEffect, useRef, useState } from "react";

import { ArrowUp, CornerDownLeft, LoaderCircle, Sparkles } from "lucide-react";

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const MAX_LENGTH = 4000;

export function MessageInput({ onSend, disabled = false }: MessageInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const hasMessage = message.trim().length > 0;
  const showCharacterCount = message.length >= 3000;

  const resizeTextarea = () => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    textarea.style.height = "0px";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 144)}px`;
  };

  useEffect(() => {
    resizeTextarea();
  }, [message]);

  const handleSubmit = () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || disabled) {
      return;
    }

    onSend(trimmedMessage);
    setMessage("");
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Prevent Enter from submitting while an IME/composition is active.
    if (event.nativeEvent.isComposing) {
      return;
    }

    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(event.target.value);
  };

  return (
    <div className="w-full shrink-0 px-4 pb-4 pt-3 sm:px-6 sm:pb-6">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          handleSubmit();
        }}
        className="mx-auto w-full max-w-[820px]"
      >
        <div
          className={[
            "rounded-[22px] border bg-white shadow-[0_12px_32px_rgba(25,61,67,0.06)] transition-[border-color,box-shadow]",
            "border-[#cfdfdc]",
            "focus-within:border-[#42a99d]",
            "focus-within:shadow-[0_0_0_4px_rgba(20,184,166,0.10),0_16px_32px_rgba(25,61,67,0.09)]",
            disabled ? "opacity-75" : "",
          ].join(" ")}
        >
          <div className="flex items-center gap-2 border-b border-[#edf2f0] px-4 pb-2.5 pt-3">
            <Sparkles size={14} className="text-[#138d80]" aria-hidden="true" />
            <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#577174]">
              Ask NexaTel AI
            </span>
            <span className="ml-auto text-[10px] text-[#a0aeae]">Account-aware</span>
          </div>

          <div className="flex items-end gap-3 px-4 py-3">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              rows={1}
              maxLength={MAX_LENGTH}
              aria-label="Message"
              placeholder="Ask about your plan, usage, bill, payments, tickets..."
              className={[
                "min-h-12 max-h-36 flex-1 resize-none overflow-y-auto",
                "bg-transparent px-0 py-1",
                "text-[15px] leading-6 text-slate-800",
                "outline-none",
                "placeholder:text-slate-400",
                "disabled:cursor-not-allowed disabled:placeholder:text-slate-300",
                "[scrollbar-width:thin]",
              ].join(" ")}
            />

            <button
              type="submit"
              disabled={disabled || !hasMessage}
              aria-label={disabled ? "Sending message" : "Send message"}
              aria-busy={disabled}
              className={[
                "grid h-10 w-10 shrink-0 place-items-center rounded-xl",
                "transition-colors duration-150",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2",
                hasMessage && !disabled
                  ? "bg-slate-900 text-white hover:bg-slate-800 active:bg-slate-950"
                  : "cursor-not-allowed bg-slate-100 text-slate-400",
              ].join(" ")}
            >
              {disabled ? (
                <LoaderCircle size={17} className="animate-spin" aria-hidden="true" />
              ) : (
                <ArrowUp size={17} strokeWidth={2.4} aria-hidden="true" />
              )}
            </button>
          </div>

          {showCharacterCount && (
            <div className="flex justify-end px-4 pb-2.5">
              <span className="text-[11px] tabular-nums text-slate-400">
                {message.length.toLocaleString()}/{MAX_LENGTH.toLocaleString()}
              </span>
            </div>
          )}
        </div>

        <div className="mt-2 flex items-center justify-between px-1 text-[11px] text-slate-400">
          <span className="hidden sm:inline">Answers grounded in your selected account</span>

          <span className="ml-auto flex items-center gap-1.5">
            <CornerDownLeft size={12} aria-hidden="true" />
            Enter to send
            <span className="text-slate-300">·</span>
            Shift + Enter for a new line
          </span>
        </div>
      </form>
    </div>
  );
}
