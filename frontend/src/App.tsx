import { useEffect, useRef, useState } from "react";

import {
  CircleAlert,
  Database,
  MessagesSquare,
  Plus,
  Signal,
  UserRound,
} from "lucide-react";

import { ChatWindow } from "./components/ChatWindow";
import { CustomerSelector } from "./components/CustomerSelector";
import { MessageInput } from "./components/MessageInput";
import { WelcomePanel } from "./components/WelcomePanel";
import { DatabaseExplorerPage } from "./pages/DatabaseExplorerPage";
import {
  getAccountSnapshot,
  getCustomerProfile,
  getDemoCustomers,
  resetConversationContext,
  streamChatMessage,
} from "./services/api";

import type {
  AccountSnapshot,
  CustomerProfile,
  DemoCustomer,
} from "./types/account";
import type { ChatMessage } from "./types/chat";

type AppPage = "support" | "database";

function createMessageId(): string {
  return `${Date.now()}-${Math.random()
    .toString(36)
    .slice(2)}`;
}

function createConversationId(): string {
  return globalThis.crypto?.randomUUID?.()
    ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function headerTitle(appPage: AppPage): string {
  if (appPage === "database") {
    return "Database viewer";
  }

  return "Account support";
}

export default function App() {
  const [appPage, setAppPage] = useState<AppPage>("support");
  const [customerId, setCustomerId] = useState("CUST001");
  const [conversationId, setConversationId] = useState(createConversationId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [snapshot, setSnapshot] = useState<AccountSnapshot | null>(null);
  const [snapshotLoading, setSnapshotLoading] = useState(true);
  const [demoCustomers, setDemoCustomers] = useState<DemoCustomer[]>([]);

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    setSnapshotLoading(true);

    void Promise.all([
      getCustomerProfile(customerId, controller.signal),
      getAccountSnapshot(customerId, controller.signal),
    ])
      .then(([nextProfile, nextSnapshot]) => {
        setProfile(nextProfile);
        setSnapshot(nextSnapshot);
      })
      .catch((profileError: unknown) => {
        if (
          profileError instanceof DOMException
          && profileError.name === "AbortError"
        ) {
          return;
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setSnapshotLoading(false);
        }
      });

    return () => controller.abort();
  }, [customerId]);

  useEffect(() => {
    const controller = new AbortController();

    void getDemoCustomers(controller.signal)
      .then(setDemoCustomers)
      .catch(() => {
        // Demo list is optional for the selector fallback.
      });

    return () => controller.abort();
  }, []);

  const hasConversation = messages.length > 0;
  const displayName = profile?.name ?? customerId;

  const handleCustomerChange = (nextCustomerId: string) => {
    void resetConversationContext(customerId, conversationId);

    setCustomerId(nextCustomerId);
    setConversationId(createConversationId());
    setMessages([]);
    setError(null);
  };

  const handleNewConversation = () => {
    if (loading) {
      return;
    }

    void resetConversationContext(customerId, conversationId);

    setConversationId(createConversationId());
    setMessages([]);
    setError(null);
    setAppPage("support");
  };

  const handleSend = async (messageText: string) => {
    const trimmedMessage = messageText.trim();

    if (!trimmedMessage || loading) {
      return;
    }

    setError(null);
    setAppPage("support");

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content: trimmedMessage,
      createdAt: new Date(),
    };
    const assistantMessageId = createMessageId();
    const abortController = new AbortController();
    let streamedText = "";
    let widgetOnlyResponse = false;
    let useMetadataMessageOnly = false;
    abortControllerRef.current = abortController;

    setMessages((current) => [
      ...current,
      userMessage,
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        createdAt: new Date(),
        isStreaming: true,
      },
    ]);

    setLoading(true);

    try {
      await streamChatMessage(
        customerId,
        trimmedMessage,
        conversationId,
        {
          onMetadata: (response) => {
            widgetOnlyResponse =
              response.presentation?.type === "customer_360";
            const metadataMessage = response.message?.trim() ?? "";
            useMetadataMessageOnly =
              !widgetOnlyResponse && metadataMessage.length > 0;

            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? {
                      ...message,
                      content: widgetOnlyResponse
                        ? ""
                        : metadataMessage || message.content,
                      status: response.status,
                      source: response.source,
                      presentation: response.presentation,
                      options: response.options,
                    }
                  : message,
              ),
            );
          },
          onText: (text) => {
            if (widgetOnlyResponse || useMetadataMessageOnly) {
              return;
            }

            streamedText += text;
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? { ...message, content: message.content + text }
                  : message,
              ),
            );
          },
        },
        abortController.signal,
      );

      setMessages((current) =>
        current.map((message) =>
          message.id === assistantMessageId
            ? { ...message, isStreaming: false }
            : message,
        ),
      );
    } catch (requestError) {
      const wasAborted = abortController.signal.aborted;
      const errorMessage =
        requestError instanceof Error
          ? requestError.message
          : (
              "We could not reach the NexaTel support service. " +
              "Please try again."
            );

      setMessages((current) =>
        current.flatMap((message) => {
          if (message.id !== assistantMessageId) {
            return [message];
          }

          return streamedText
            ? [{ ...message, isStreaming: false }]
            : [];
        }),
      );

      if (!wasAborted) {
        setError(errorMessage);
      }
    } finally {
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }

      setLoading(false);
    }
  };

  const handleStop = () => {
    abortControllerRef.current?.abort();
  };

  const sharedHeader = (
    <header className="surface-header flex h-14 shrink-0 items-center justify-between gap-3 border-b border-[var(--color-line)] px-4 sm:px-6">
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-semibold tracking-tight text-[var(--color-ink)]">
          {headerTitle(appPage)}
        </p>
        <p className="text-[11px] text-[var(--color-muted)]">
          {appPage === "database"
            ? "Read-only nexatel.db — browse with search and filters"
            : (profile?.phone_masked ?? "Select a customer")}
        </p>
      </div>

      <CustomerSelector
        customerId={customerId}
        customers={demoCustomers}
        onCustomerChange={handleCustomerChange}
        disabled={loading}
      />
    </header>
  );

  return (
    <div className="app-shell flex h-dvh min-h-0 overflow-hidden font-sans text-[var(--color-ink)]">
      <aside className="surface-sidebar hidden w-[220px] shrink-0 flex-col border-r border-[var(--color-line)] lg:flex">
        <div className="flex h-16 items-center gap-3 border-b border-[var(--color-line)] px-4">
          <span className="grid size-9 place-items-center rounded-lg bg-white text-[var(--color-brand)] shadow-sm ring-1 ring-[var(--color-line)]">
            <Signal size={17} strokeWidth={2} aria-hidden="true" />
          </span>
          <div>
            <span className="block text-[15px] font-semibold tracking-tight text-[var(--color-brand)]">
              NexaTel
            </span>
            <span className="mt-0.5 block text-[10px] text-[var(--color-muted)]">
              Self-care demo
            </span>
          </div>
        </div>

        {appPage === "support" && (
          <div className="px-3 pt-4">
            <button
              type="button"
              onClick={handleNewConversation}
              disabled={loading}
              className={[
                "flex h-9 w-full items-center justify-center gap-2 rounded-lg",
                "bg-[var(--color-brand)] px-3 text-[12px] font-medium text-white",
                "shadow-sm transition hover:bg-[var(--color-brand-hover)]",
                "disabled:opacity-40",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2f654f]/40",
              ].join(" ")}
            >
              <Plus size={14} strokeWidth={2} aria-hidden="true" />
              New chat
            </button>
          </div>
        )}

        <nav className="space-y-0.5 px-3 pt-4" aria-label="Workspace">
          <p className="px-3 pb-1.5 text-[10px] font-medium uppercase tracking-wide text-[#8a968d]">
            Workspace
          </p>
          <button
            type="button"
            onClick={() => setAppPage("support")}
            className="ui-nav-item"
            data-active={appPage === "support" ? "true" : undefined}
          >
            <MessagesSquare size={15} strokeWidth={1.8} aria-hidden="true" />
            Support
          </button>
          <button
            type="button"
            onClick={() => setAppPage("database")}
            className="ui-nav-item"
            data-active={appPage === "database" ? "true" : undefined}
          >
            <Database size={15} strokeWidth={1.8} aria-hidden="true" />
            Database
          </button>
        </nav>

        <div className="mt-auto border-t border-[#e3e9e4] px-4 py-4">
          <div className="flex items-center gap-3 px-2 py-1.5">
            <span className="grid size-8 shrink-0 place-items-center rounded-md bg-white text-[#52715d] ring-1 ring-[#dfe7e0]">
              <UserRound size={16} strokeWidth={1.8} aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <span className="block text-[10px] text-[#7a897f]">
                Demo account
              </span>
              <span className="mt-0.5 block truncate text-[11px] font-semibold text-[#2c4336]">
                {displayName}
              </span>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        {appPage === "database" ? (
          <>
            {sharedHeader}
            <main className="chat-canvas flex min-h-0 flex-1 flex-col overflow-hidden">
              <DatabaseExplorerPage customerId={customerId} />
            </main>
          </>
        ) : (
          <>
            {sharedHeader}
            <main
              id="conversation"
              aria-busy={loading}
              className="chat-canvas flex min-h-0 flex-1 flex-col overflow-hidden"
            >
              <div className="mx-auto flex h-full min-h-0 w-full min-w-0 max-w-[800px] flex-col overflow-x-hidden">
                {!hasConversation ? (
                  <WelcomePanel
                    name={displayName}
                    snapshot={snapshot}
                    loading={snapshotLoading}
                    onPrompt={handleSend}
                    disabled={loading}
                  />
                ) : (
                  <ChatWindow
                    messages={messages}
                    loading={loading}
                    onOptionSelect={handleSend}
                  />
                )}

                {error && (
                  <div className="shrink-0 px-4 pb-2">
                    <div
                      role="alert"
                      className="flex items-start gap-2.5 rounded-md border border-[#eed5d0] bg-[#fff8f6] px-3.5 py-3 text-[11px] text-[#874b43]"
                    >
                      <CircleAlert size={15} className="mt-0.5 shrink-0" aria-hidden="true" />
                      <span>{error}</span>
                    </div>
                  </div>
                )}

                <div className="shrink-0">
                  <MessageInput
                    onSend={handleSend}
                    onStop={handleStop}
                    disabled={loading}
                  />
                </div>
              </div>
            </main>
          </>
        )}

        <nav
          className="surface-header flex shrink-0 gap-1 border-t border-[var(--color-line)] px-2 py-1.5 lg:hidden"
          aria-label="Mobile navigation"
        >
          <button
            type="button"
            onClick={() => setAppPage("support")}
            className={[
              "flex flex-1 flex-col items-center gap-0.5 rounded-lg py-2 text-[10px] font-semibold transition",
              appPage === "support"
                ? "bg-white text-[var(--color-brand)] shadow-sm ring-1 ring-[var(--color-line)]"
                : "text-[#96a198]",
            ].join(" ")}
          >
            <MessagesSquare size={16} aria-hidden="true" />
            Support
          </button>
          <button
            type="button"
            onClick={() => setAppPage("database")}
            className={[
              "flex flex-1 flex-col items-center gap-0.5 rounded-lg py-2 text-[10px] font-semibold transition",
              appPage === "database"
                ? "bg-white text-[var(--color-brand)] shadow-sm ring-1 ring-[var(--color-line)]"
                : "text-[#96a198]",
            ].join(" ")}
          >
            <Database size={16} aria-hidden="true" />
            Data
          </button>
        </nav>
      </div>
    </div>
  );
}
