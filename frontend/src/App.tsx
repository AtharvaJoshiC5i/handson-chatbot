import { useState } from "react";

import { Plus } from "lucide-react";

import { ChatWindow } from "./components/ChatWindow";
import { CustomerSelector } from "./components/CustomerSelector";
import { MessageInput } from "./components/MessageInput";
import { sendChatMessage } from "./services/api";

import type { ChatMessage } from "./types/chat";

const starterPrompts = [
  "Check my current plan",
  "Review my data usage",
  "Show my latest bill",
  "Help with a payment",
];

function createMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function App() {
  const [customerId, setCustomerId] = useState("CUST001");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasConversation = messages.length > 0;

  const handleCustomerChange = (nextCustomerId: string) => {
    setCustomerId(nextCustomerId);
    setMessages([]);
    setError(null);
  };

  const handleNewConversation = () => {
    if (loading) {
      return;
    }

    setMessages([]);
    setError(null);
  };

  const handleSend = async (messageText: string) => {
    const trimmedMessage = messageText.trim();

    if (!trimmedMessage || loading) {
      return;
    }

    setError(null);

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content: trimmedMessage,
      createdAt: new Date(),
    };

    setMessages((current) => [...current, userMessage]);
    setLoading(true);

    try {
      const response = await sendChatMessage(customerId, trimmedMessage);

      const assistantMessage: ChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content: response.message,
        status: response.status,
        source: response.source,
        options: response.options,
        createdAt: new Date(),
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (requestError) {
      const errorMessage =
        requestError instanceof Error
          ? requestError.message
          : "We could not reach the NexaTel support service. Please try again.";

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-dvh min-h-0 overflow-hidden bg-white font-sans text-[#202725]">
      {/* Sidebar */}
      <aside className="hidden w-[216px] shrink-0 flex-col border-r border-[#e6e9e7] bg-[#f7f8f7] lg:flex">
        <div className="flex h-14 items-center px-4">
          <span className="text-[13px] font-semibold tracking-[-0.015em] text-[#242b29]">
            NexaTel
          </span>
        </div>

        <div className="px-2.5 pt-2">
          <button
            type="button"
            onClick={handleNewConversation}
            disabled={loading}
            className={[
              "flex h-9 w-full items-center gap-2 rounded-md px-2.5",
              "text-[12px] font-medium text-[#4d5754]",
              "transition-colors duration-150",
              "hover:bg-[#ecefed] hover:text-[#202725]",
              "focus-visible:outline-none",
              "focus-visible:ring-2",
              "focus-visible:ring-[#afb7b3]",
              "disabled:pointer-events-none disabled:opacity-40",
            ].join(" ")}
          >
            <Plus
              size={14}
              strokeWidth={2}
              className="text-[#68716e]"
              aria-hidden="true"
            />

            <span>New conversation</span>
          </button>
        </div>

        <nav className="px-2.5 pt-5" aria-label="Conversations">
          <p className="px-2.5 pb-1.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#949c99]">
            Workspace
          </p>

          <button
            type="button"
            onClick={() => {
              if (!loading) {
                setMessages([]);
                setError(null);
              }
            }}
            className={[
              "flex h-8 w-full items-center gap-2 rounded-md px-2.5",
              "bg-[#e9ecea]",
              "text-left text-[12px] font-medium text-[#303836]",
              "transition-colors duration-150",
              "hover:bg-[#e3e7e5]",
            ].join(" ")}
          >
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#626b68]"
              aria-hidden="true"
            />

            <span className="truncate">Support assistant</span>
          </button>
        </nav>

        <div className="mt-auto border-t border-[#e6e9e7] px-4 py-3">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10px] text-[#8c9692]">Customer</span>

            <span className="text-[10px] font-medium tabular-nums text-[#58625e]">
              {customerId}
            </span>
          </div>
        </div>
      </aside>

      {/* Main application */}
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        {/* Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-[#e6e9e7] bg-white px-4 sm:px-5">
          <div className="min-w-0">
            <span className="text-[12px] font-medium text-[#38413e]">
              Support assistant
            </span>
          </div>

          <div id="customer-context" className="flex items-center gap-2">
            <span className="hidden text-[11px] text-[#8b9491] sm:block">
              Customer
            </span>

            <CustomerSelector
              customerId={customerId}
              onCustomerChange={handleCustomerChange}
              disabled={loading}
            />
          </div>
        </header>

        {/* Conversation */}
        <main
          id="conversation"
          aria-busy={loading}
          className="min-h-0 flex-1 overflow-hidden bg-white"
        >
          <div className="mx-auto flex h-full w-full max-w-[720px] flex-col">
            {!hasConversation ? (
              <div className="flex min-h-0 flex-1 flex-col justify-center px-5 pb-10 pt-8 sm:px-6">
                <section className="w-full max-w-[600px]">
                  <p className="text-[10px] font-medium uppercase tracking-[0.08em] text-[#929b97]">
                    Customer {customerId}
                  </p>

                  <h1 className="mt-2 text-[24px] font-semibold tracking-[-0.04em] text-[#202725]">
                    How can I help?
                  </h1>

                  <p className="mt-2 max-w-[500px] text-[13px] leading-5 text-[#7a8581]">
                    Ask about your plan, usage, billing, payments, support
                    tickets, or devices.
                  </p>

                  <div
                    className="mt-6 grid max-w-[560px] grid-cols-1 sm:grid-cols-2"
                    aria-label="Suggested questions"
                  >
                    {starterPrompts.map((prompt, index) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => handleSend(prompt)}
                        disabled={loading}
                        className={[
                          "flex min-h-9 items-center justify-between",
                          "border-b border-[#e8ebe9]",
                          index % 2 === 0 ? "sm:mr-5" : "sm:ml-5",
                          "py-2 text-left",
                          "text-[12px] font-medium text-[#59625f]",
                          "transition-colors duration-150",
                          "hover:text-[#202725]",
                          "focus-visible:outline-none",
                          "focus-visible:ring-2",
                          "focus-visible:ring-inset",
                          "focus-visible:ring-[#adb6b2]",
                          "disabled:pointer-events-none",
                          "disabled:opacity-40",
                        ].join(" ")}
                      >
                        <span>{prompt}</span>

                        <span
                          className="ml-4 text-[#a1a9a6]"
                          aria-hidden="true"
                        >
                          →
                        </span>
                      </button>
                    ))}
                  </div>
                </section>
              </div>
            ) : (
              <ChatWindow
                messages={messages}
                loading={loading}
                onOptionSelect={handleSend}
              />
            )}

            {error && (
              <div className="shrink-0 px-4 pb-2 sm:px-6">
                <div
                  role="alert"
                  className={[
                    "rounded-md border border-[#eadbd8]",
                    "bg-[#fdfafa]",
                    "px-3 py-2",
                    "text-[11px] leading-5 text-[#875650]",
                  ].join(" ")}
                >
                  {error}
                </div>
              </div>
            )}

            <MessageInput onSend={handleSend} disabled={loading} />
          </div>
        </main>
      </div>
    </div>
  );
}
