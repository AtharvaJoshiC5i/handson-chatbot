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

  const lastAssistantMessageId = messages
    .filter((message) => message.role === "assistant")
    .at(-1)?.id;

  function priorUserMessage(
    messageIndex: number,
  ): string {
    for (let index = messageIndex - 1; index >= 0; index -= 1) {
      if (messages[index].role === "user") {
        return messages[index].content;
      }
    }
    return "";
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain scrollbar-none [&::-webkit-scrollbar]:hidden">
      <div className="mx-auto flex w-full max-w-[760px] flex-col gap-7 px-4 py-7 sm:px-6 sm:py-8">
        {messages.map(
          (message, messageIndex) => (
            <MessageBubble
              key={message.id}
              message={message}
              showFollowUps={
                !loading
                && message.role === "assistant"
                && message.id === lastAssistantMessageId
              }
              userMessageForFollowUps={priorUserMessage(
                messageIndex,
              )}
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