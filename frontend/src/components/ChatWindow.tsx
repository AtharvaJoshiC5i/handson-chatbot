import { useEffect, useRef } from "react";

import { Bot } from "lucide-react";

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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-5 sm:px-8 sm:py-6">
      <div className="mx-auto flex w-full max-w-190 flex-col gap-7">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onOptionSelect={onOptionSelect}
            optionsDisabled={loading}
          />
        ))}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="grid size-8 shrink-0 place-items-center rounded-xl bg-[#123442] text-sm text-white shadow-sm shadow-[#123442]/20">
              <Bot size={16} strokeWidth={2.2} aria-hidden="true" />
            </div>
            <div className="pt-1 text-sm leading-7 text-[#71858a]">
              NexaTel AI is thinking{" "}
              <span className="animate-pulse tracking-[0.18em] text-[#138d80]">
                •••
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
