import { useEffect, useRef, useState } from "react";
import { ArrowUp, Square } from "lucide-react";

interface MessageInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
}

const MAX_LENGTH = 4000;
const MAX_HEIGHT = 160;

export function MessageInput({ onSend, onStop, disabled = false }: MessageInputProps) {
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
    <div className="w-full shrink-0 px-4 pb-4 pt-3 sm:px-8 sm:pb-6">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          handleSubmit();
        }}
        className="mx-auto w-full max-w-[800px]"
      >
        <div
          className={[
            "relative rounded-xl border bg-white",
            "border-[#dce5de]",
            "shadow-[0_2px_8px_rgba(23,60,50,0.04),0_8px_24px_rgba(23,60,50,0.035)]",
            "transition-[border-color,box-shadow] duration-150",
            "hover:border-[#bfd0c3]",
            "focus-within:border-[#789884]",
            "focus-within:shadow-[0_0_0_3px_rgba(47,101,79,0.08),0_8px_24px_rgba(23,60,50,0.06)]",
            disabled ? "bg-[#f8faf8]" : "",
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
              placeholder="Message NexaTel support..."
              className={[
                "min-h-10 max-h-[160px] flex-1",
                "resize-none overflow-y-auto",
                "bg-transparent",
                "px-2.5 py-2",
                "text-[14px] leading-6 text-[#263a30]",
                "placeholder:text-[#8a988f]",
                "outline-none",
                "disabled:cursor-not-allowed",
                "disabled:placeholder:text-[#b9bec1]",
                "[scrollbar-width:thin]",
              ].join(" ")}
            />

            <button
              type={disabled ? "button" : "submit"}
              onClick={disabled ? onStop : undefined}
              disabled={disabled ? !onStop : !canSend}
              aria-label={disabled ? "Stop generating response" : "Send message"}
              aria-busy={disabled}
              className={[
                "mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center",
                "rounded-full",
                "transition-[background-color,color,transform] duration-150",
                "focus-visible:outline-none",
                "focus-visible:ring-2 focus-visible:ring-[#285647]",
                "focus-visible:ring-offset-2",
                canSend
                  ? "bg-[#173c32] text-white hover:bg-[#245344] active:scale-[0.96]"
                  : "cursor-not-allowed bg-[#e9efea] text-[#99a79c]",
              ].join(" ")}
            >
              {disabled ? (
                <Square size={12} strokeWidth={2.4} fill="currentColor" aria-hidden="true" />
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
