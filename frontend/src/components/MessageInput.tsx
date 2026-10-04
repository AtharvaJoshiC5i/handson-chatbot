import { useEffect, useRef, useState } from "react";
import { ArrowUp, Square } from "lucide-react";

interface MessageInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
}

const MAX_LENGTH = 4000;
const MAX_HEIGHT = 160;

export function MessageInput({
  onSend,
  onStop,
  disabled = false,
}: MessageInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const trimmed = message.trim();
  const canSend = trimmed.length > 0 && !disabled;
  const isGenerating = disabled;

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
    if (!trimmed || disabled) {
      return;
    }

    onSend(trimmed);
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

  const sendActive = isGenerating ? Boolean(onStop) : canSend;

  return (
    <div className="composer-dock w-full shrink-0">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (isGenerating) {
            onStop?.();
            return;
          }

          handleSubmit();
        }}
        className="mx-auto w-full max-w-[680px]"
      >
        <div
          className="composer-field"
          data-busy={isGenerating ? "true" : "false"}
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isGenerating}
            rows={1}
            maxLength={MAX_LENGTH}
            aria-label="Message"
            placeholder="Ask about your plan, usage, bills, or payments…"
            className={[
              "max-h-[160px] min-h-[38px] flex-1 resize-none",
              "bg-transparent py-2 pr-1",
              "text-[13.5px] leading-[1.45] text-[var(--color-ink)]",
              "placeholder:text-[#9aa89f]",
              "outline-none",
              "[scrollbar-width:thin]",
              "disabled:cursor-not-allowed disabled:text-[var(--color-muted)]",
            ].join(" ")}
          />

          <button
            type={isGenerating ? "button" : "submit"}
            onClick={isGenerating ? onStop : undefined}
            disabled={!sendActive}
            data-active={sendActive ? "true" : "false"}
            aria-label={
              isGenerating ? "Stop generating response" : "Send message"
            }
            aria-busy={isGenerating}
            className="composer-send"
          >
            {isGenerating ? (
              <Square
                size={10}
                strokeWidth={0}
                fill="currentColor"
                aria-hidden="true"
              />
            ) : (
              <ArrowUp size={17} strokeWidth={2.25} aria-hidden="true" />
            )}
          </button>
        </div>

        <p className="composer-footnote">
          Answers are sourced from your account records. Confirm critical details
          before acting.
        </p>
      </form>
    </div>
  );
}
