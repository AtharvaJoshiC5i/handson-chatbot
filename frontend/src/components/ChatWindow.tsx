import {
  useEffect,
  useRef,
} from "react";

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
  const bottomRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [
    messages,
    loading,
  ]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain scrollbar-none [&::-webkit-scrollbar]:hidden">
      <div className="mx-auto flex w-full max-w-[800px] flex-col gap-8 px-5 py-8 sm:px-8">
        {messages.map(
          (message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onOptionSelect={
                onOptionSelect
              }
              optionsDisabled={
                loading
              }
            />
          ),
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}