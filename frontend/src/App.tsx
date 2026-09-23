import { useState } from "react";

import {
  ChevronDown,
  MessageSquarePlus,
  PanelLeft,
  Plus,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { ChatWindow } from "./components/ChatWindow";

import { CustomerSelector } from "./components/CustomerSelector";

import { MessageInput } from "./components/MessageInput";

import { sendChatMessage } from "./services/api";

import type { ChatMessage } from "./types/chat";

function createMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function createWelcomeMessage(): ChatMessage {
  return {
    id: createMessageId(),
    role: "assistant",
    content:
      "Hello! I’m the NexaTel AI support assistant. Ask me about your current plan, account status, usage, bills, payments, support tickets, or device information.",
    createdAt: new Date(),
  };
}

export default function App() {
  const [customerId, setCustomerId] = useState("CUST001");

  const [messages, setMessages] = useState<ChatMessage[]>([
    createWelcomeMessage(),
  ]);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const handleCustomerChange = (nextCustomerId: string) => {
    setCustomerId(nextCustomerId);
    setError(null);

    setMessages([
      {
        id: createMessageId(),
        role: "assistant",
        content: `Customer context switched to ${nextCustomerId}. What would you like to know?`,
        createdAt: new Date(),
      },
    ]);
  };

  const handleSend = async (messageText: string) => {
    if (loading) {
      return;
    }

    setError(null);

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content: messageText,
      createdAt: new Date(),
    };

    setMessages((current) => [...current, userMessage]);

    setLoading(true);

    try {
      const response = await sendChatMessage(customerId, messageText);

      const assistantMessage: ChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content: response.message,
        status: response.status,
        source: response.source,
        createdAt: new Date(),
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (requestError) {
      const errorMessage =
        requestError instanceof Error
          ? requestError.message
          : "Something went wrong while contacting the NexaTel backend.";

      setError(errorMessage);

      setMessages((current) => [
        ...current,
        {
          id: createMessageId(),
          role: "assistant",
          content: errorMessage,
          status: "API_ERROR",
          createdAt: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-dvh overflow-hidden bg-[#f5f8f7] font-sans text-[#17313d]">
      <aside className="hidden h-full w-64 shrink-0 flex-col border-r border-[#dfe8e5] bg-[#eef4f1] px-4 py-5 lg:flex">
        <div className="flex items-center gap-3 px-2 pb-8">
          <div className="grid size-9 place-items-center rounded-xl bg-[#123442] text-sm font-bold text-white shadow-lg shadow-[#123442]/15">
            <Sparkles size={17} strokeWidth={2.2} aria-hidden="true" />
          </div>
          <div>
            <p className="m-0 text-[10px] font-bold uppercase tracking-[0.18em] text-[#138d80]">
              NexaTel
            </p>
            <p className="m-0 text-sm font-bold text-[#17313d]">Concierge</p>
          </div>
        </div>

        <button
          className="flex w-full items-center gap-2.5 rounded-xl border border-[#c8dad5] bg-white px-3 py-2.5 text-left text-xs font-bold text-[#17313d] shadow-sm shadow-[#2a6158]/5 transition hover:-translate-y-0.5 hover:border-[#75b9ad]"
          type="button"
          onClick={() => setMessages([createWelcomeMessage()])}
        >
          <Plus size={16} strokeWidth={2.4} className="text-[#138d80]" aria-hidden="true" />
          New conversation
        </button>

        <nav className="mt-8" aria-label="Workspace">
          <span className="mb-2 block px-3 text-[10px] font-bold uppercase tracking-[0.14em] text-[#98a9a9]">
            Workspace
          </span>
          <a
            className="flex items-center gap-3 rounded-lg bg-[#dfede8] px-3 py-2.5 text-xs font-bold text-[#17313d]"
            href="#conversation"
          >
            <MessageSquarePlus size={15} className="text-[#138d80]" aria-hidden="true" />
            Support assistant
          </a>
        </nav>
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="shrink-0 border-b border-[#dfe8e5] bg-white/85 backdrop-blur-xl">
          <div className="flex h-[68px] items-center justify-between gap-5 px-5 sm:px-8">
            <div className="flex items-center gap-2.5 text-sm font-bold text-[#17313d] lg:hidden">
              <div className="grid size-8 place-items-center rounded-lg bg-[#123442] text-xs text-white">
                <Sparkles size={15} strokeWidth={2.2} aria-hidden="true" />
              </div>
              NexaTel AI
            </div>

            <div className="hidden items-center gap-3 text-sm font-bold text-[#17313d] lg:flex">
              <PanelLeft size={17} className="text-[#138d80]" aria-hidden="true" />
              <span>NexaTel AI</span>
              <span className="h-4 w-px bg-[#dfe8e5]" aria-hidden="true" />
              <span className="text-xs font-medium text-[#7d9193]">Support workspace</span>
              <ChevronDown size={14} className="text-[#99a9a9]" aria-hidden="true" />
            </div>

            <div className="flex items-center gap-3" id="customer-context">
              <div className="hidden items-center gap-1.5 rounded-full border border-[#d8e8e3] bg-[#f4faf7] px-2.5 py-1.5 text-[10px] font-semibold text-[#398070] sm:flex">
                <ShieldCheck size={13} strokeWidth={2.2} aria-hidden="true" />
                Secure context
              </div>
              <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#849596]">
                Context
              </span>
              <CustomerSelector
                customerId={customerId}
                onCustomerChange={handleCustomerChange}
                disabled={loading}
              />
            </div>
          </div>
        </header>

        <main
          className="flex min-h-0 flex-1 flex-col overflow-hidden"
          id="conversation"
        >
          <div className="flex min-h-0 flex-1 flex-col">
            <div className="mx-auto w-full max-w-[860px] shrink-0 px-5 pb-5 pt-8 sm:px-8 sm:pt-10">
              <h2 className="m-0 text-xl font-semibold tracking-[-0.02em] text-[#17313d] sm:text-2xl">
                How can we help today?
              </h2>
              <p className="mt-2 text-xs text-[#71858a]">
                Answers grounded in the account for {customerId}
              </p>
            </div>

            {error && (
              <div className="mx-auto w-full max-w-[860px] border-y border-red-200 bg-red-50 px-5 py-3 text-sm text-red-700 sm:px-8">
                {error}
              </div>
            )}

            <ChatWindow messages={messages} loading={loading} />

            <MessageInput onSend={handleSend} disabled={loading} />
          </div>
        </main>
      </div>
    </div>
  );
}
