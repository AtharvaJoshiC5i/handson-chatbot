import { useState } from "react";

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
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <div className="flex items-center gap-3">
            <div className="brand-mark">N</div>

            <div>
              <p className="brand-kicker">NexaTel / concierge</p>
              <h1 className="brand-title">AI Customer Support</h1>
              <p className="brand-subtitle">
                Private account intelligence, on demand
              </p>
            </div>
          </div>

          <div className="header-status">
            <span className="status-dot" />
            Secure session
          </div>
          <div className="w-32 sm:w-40">
            <CustomerSelector
              customerId={customerId}
              onCustomerChange={handleCustomerChange}
              disabled={loading}
            />
          </div>
        </div>
      </header>

      <main className="workspace">
        <div className="chat-frame">
          <div className="chat-toolbar">
            <div>
              <h2 className="toolbar-label">Your support desk</h2>
              <p className="toolbar-context">
                Verified context for {customerId}
              </p>
            </div>
            <div className="toolbar-badge">
              <span className="status-dot" /> Live connection
            </div>
          </div>

          {error && (
            <div className="border-b border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 sm:px-6">
              {error}
            </div>
          )}

          <ChatWindow messages={messages} loading={loading} />

          <MessageInput onSend={handleSend} disabled={loading} />
        </div>
      </main>
    </div>
  );
}
