import { useEffect, useRef } from "react";

import type { ChatMessage } from "../types/chat";

import { MessageBubble } from "./MessageBubble";

interface ChatWindowProps {
  messages: ChatMessage[];
  loading?: boolean;
  onOptionSelect?: (message: string) => void;
}

export function ChatWindow({
  messages,
  loading = false,
  onOptionSelect,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const hasRenderedMessages = useRef(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: hasRenderedMessages.current ? "smooth" : "auto",
      block: "end",
    });

    hasRenderedMessages.current = true;
  }, [messages.length, loading]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
      <div className="mx-auto w-full max-w-[680px] px-4 pb-8 pt-6 sm:px-6">
        <div className="flex flex-col gap-7 sm:gap-8">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onOptionSelect={onOptionSelect}
              optionsDisabled={loading}
            />
          ))}

          {loading && (
            <div
              role="status"
              aria-live="polite"
              aria-label="Assistant is responding"
              className="flex min-h-6 items-center"
            >
              <div className="flex items-center gap-1.5" aria-hidden="true">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#a6a6a2]" />

                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#a6a6a2] [animation-delay:150ms]" />

                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#a6a6a2] [animation-delay:300ms]" />
              </div>
            </div>
          )}

          <div
            ref={bottomRef}
            aria-hidden="true"
            className="h-px"
          />
        </div>
      </div>
    </div>
  );
}