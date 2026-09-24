import { useEffect, useRef, useState } from "react";
import { ArrowUp, LoaderCircle } from "lucide-react";

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const MAX_LENGTH = 4000;
const MAX_HEIGHT = 160;

export function MessageInput({ onSend, disabled = false }: MessageInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canSend = message.trim().length > 0 && !disabled;

  const resizeTextarea = () => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, MAX_HEIGHT)}px`;
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

    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.nativeEvent.isComposing) {
      return;
    }

    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full shrink-0 px-4 pb-5 pt-3 sm:px-6 sm:pb-6">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          handleSubmit();
        }}
        className="mx-auto w-full max-w-[780px]"
      >
        <div
          className={[
            "relative rounded-[20px] border bg-white",
            "border-[#d9dddf]",
            "shadow-[0_1px_2px_rgba(15,23,42,0.02),0_4px_14px_rgba(15,23,42,0.04)]",
            "transition-[border-color,box-shadow] duration-150",
            "hover:border-[#c9ced1]",
            "focus-within:border-[#b9c0c3]",
            "focus-within:shadow-[0_1px_2px_rgba(15,23,42,0.03),0_5px_18px_rgba(15,23,42,0.06)]",
            disabled ? "bg-[#fafafa]" : "",
          ].join(" ")}
        >
          <div className="flex items-end gap-2 px-2.5 py-2">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              rows={1}
              maxLength={MAX_LENGTH}
              aria-label="Message"
              placeholder="Ask anything..."
              className={[
                "min-h-10 max-h-[160px] flex-1",
                "resize-none overflow-y-auto",
                "bg-transparent",
                "px-2.5 py-2",
                "text-[15px] leading-6 text-[#1f2933]",
                "placeholder:text-[#8b9499]",
                "outline-none",
                "disabled:cursor-not-allowed",
                "disabled:placeholder:text-[#b9bec1]",
                "[scrollbar-width:thin]",
              ].join(" ")}
            />

            <button
              type="submit"
              disabled={!canSend}
              aria-label={disabled ? "Sending message" : "Send message"}
              aria-busy={disabled}
              className={[
                "mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center",
                "rounded-full",
                "transition-[background-color,color,transform] duration-150",
                "focus-visible:outline-none",
                "focus-visible:ring-2 focus-visible:ring-[#1f2933]",
                "focus-visible:ring-offset-2",
                canSend
                  ? "bg-[#1f2933] text-white hover:bg-[#111827] active:scale-[0.96]"
                  : "cursor-not-allowed bg-[#eceff0] text-[#9aa1a5]",
              ].join(" ")}
            >
              {disabled ? (
                <LoaderCircle
                  size={15}
                  strokeWidth={2}
                  className="animate-spin"
                  aria-hidden="true"
                />
              ) : (
                <ArrowUp size={16} strokeWidth={2.25} aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
