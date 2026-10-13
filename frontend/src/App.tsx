import { useCallback, useEffect, useRef, useState } from "react";

import {
  CircleAlert,
  Database,
  MessagesSquare,
  Plus,
  Signal,
  UserRound,
} from "lucide-react";

import { ChatHistoryList } from "./components/ChatHistoryList";
import { ConfirmDialog } from "./components/ConfirmDialog";
import { ChatWindow } from "./components/ChatWindow";
import { CustomerSelector } from "./components/CustomerSelector";
import { MessageInput } from "./components/MessageInput";
import { ChatAccountGlance } from "./components/ChatAccountGlance";
import { WelcomePanel } from "./components/WelcomePanel";
import { DatabaseExplorerPage } from "./pages/DatabaseExplorerPage";
import { metadataCompletesStreamingTurn } from "./utils/streamingTurn";
import {
  deleteChatConversation,
  getAccountSnapshot,
  getChatConversationMessages,
  getCustomerProfile,
  getDemoCustomers,
  listChatConversations,
  resetConversationContext,
  streamChatMessage,
} from "./services/api";

import type {
  AccountSnapshot,
  CustomerProfile,
  DemoCustomer,
} from "./types/account";
import type {
  ChatConversationSummary,
  ChatMessage,
} from "./types/chat";

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
  const [chatHistory, setChatHistory] = useState<ChatConversationSummary[]>(
    [],
  );
  const [historyLoading, setHistoryLoading] = useState(true);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [deletePending, setDeletePending] =
    useState<ChatConversationSummary | null>(null);
  const [deletingConversation, setDeletingConversation] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  const refreshChatHistory = useCallback(() => {
    setHistoryLoading(true);

    void listChatConversations(customerId, "all")
      .then(setChatHistory)
      .catch(() => {
        // History is optional when the backend is offline.
      })
      .finally(() => {
        setHistoryLoading(false);
      });
  }, [customerId]);

  useEffect(() => {
    refreshChatHistory();
  }, [refreshChatHistory]);

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
  const assistantReplyInFlight = messages.some(
    (message) =>
      message.role === "assistant" && message.isStreaming,
  );
  const displayName = profile?.name ?? customerId;

  const handleCustomerChange = (nextCustomerId: string) => {
    void resetConversationContext(customerId, conversationId);

    setCustomerId(nextCustomerId);
    setConversationId(createConversationId());
    setMessages([]);
    setError(null);
  };

  const handleNewConversation = () => {
    if (loading || loadingConversation) {
      return;
    }

    void resetConversationContext(customerId, conversationId);

    setConversationId(createConversationId());
    setMessages([]);
    setError(null);
    setAppPage("support");
  };

  const handleSelectHistory = async (
    conversation: ChatConversationSummary,
  ) => {
    if (loading || loadingConversation) {
      return;
    }

    if (conversation.conversation_id === conversationId) {
      setAppPage("support");
      return;
    }

    void resetConversationContext(customerId, conversationId);

    setLoadingConversation(true);
    setError(null);
    setAppPage("support");
    setCustomerId(conversation.customer_id);
    setConversationId(conversation.conversation_id);

    try {
      const restored = await getChatConversationMessages(
        conversation.customer_id,
        conversation.conversation_id,
      );
      setMessages(restored);
    } catch (historyError: unknown) {
      setMessages([]);
      setError(
        historyError instanceof Error
          ? historyError.message
          : "Could not load this conversation.",
      );
    } finally {
      setLoadingConversation(false);
    }
  };

  const handleDeleteHistory = (
    conversation: ChatConversationSummary,
  ) => {
    if (loading || loadingConversation || deletingConversation) {
      return;
    }

    setDeletePending(conversation);
  };

  const handleCancelDeleteHistory = () => {
    if (deletingConversation) {
      return;
    }

    setDeletePending(null);
  };

  const handleConfirmDeleteHistory = async () => {
    if (!deletePending || deletingConversation) {
      return;
    }

    const conversation = deletePending;
    setDeletingConversation(true);

    try {
      await deleteChatConversation(
        conversation.customer_id,
        conversation.conversation_id,
      );

      if (conversation.conversation_id === conversationId) {
        void resetConversationContext(customerId, conversationId);
        setConversationId(createConversationId());
        setMessages([]);
        setError(null);
      }

      setDeletePending(null);
      refreshChatHistory();
    } catch (deleteError: unknown) {
      setError(
        deleteError instanceof Error
          ? deleteError.message
          : "Could not delete this conversation.",
      );
    } finally {
      setDeletingConversation(false);
    }
  };

  const handleSend = async (messageText: string) => {
    const trimmedMessage = messageText.trim();

    if (!trimmedMessage) {
      return;
    }

    abortControllerRef.current?.abort();

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
            const isChoiceList =
              response.presentation?.type === "choice_list";
            const metadataMessage = response.message?.trim() ?? "";
            const metadataEndsTurn =
              metadataCompletesStreamingTurn(response);
            useMetadataMessageOnly =
              metadataEndsTurn
              && metadataMessage.length > 0
              && !widgetOnlyResponse
              && !isChoiceList;

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
                      presentationMeta:
                        response.presentation_meta ?? null,
                      options: response.options,
                      isStreaming: metadataEndsTurn
                        ? false
                        : message.isStreaming,
                    }
                  : message,
              ),
            );

            if (metadataEndsTurn) {
              setLoading(false);
            }
          },
          onText: (text) => {
            if (widgetOnlyResponse || useMetadataMessageOnly) {
              return;
            }

            streamedText += text;
            setLoading(false);
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

          const hasVisibleReply =
            Boolean(message.content?.trim())
            || message.presentation != null
            || (message.options?.length ?? 0) > 0
            || streamedText.length > 0;

          if (!hasVisibleReply) {
            return [];
          }

          return [
            {
              ...message,
              content: message.content || streamedText,
              isStreaming: false,
            },
          ];
        }),
      );

      if (!wasAborted) {
        setError(errorMessage);
      }
    } finally {
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
        setLoading(false);
      }

      setMessages((current) =>
        current.map((message) =>
          message.id === assistantMessageId
            ? { ...message, isStreaming: false }
            : message,
        ),
      );
      refreshChatHistory();
    }
  };

  const handleStop = () => {
    abortControllerRef.current?.abort();
    setLoading(false);
    setMessages((current) =>
      current.map((message) =>
        message.role === "assistant" && message.isStreaming
          ? { ...message, isStreaming: false }
          : message,
      ),
    );
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
      <aside className="app-sidebar surface-sidebar hidden min-h-0 shrink-0 flex-col lg:flex">
        <div className="app-sidebar-brand">
          <span className="app-sidebar-brand-icon" aria-hidden="true">
            <Signal size={17} strokeWidth={2} />
          </span>
          <div className="min-w-0">
            <span className="app-sidebar-brand-title">NexaTel</span>
            <span className="app-sidebar-brand-subtitle">Self-care demo</span>
          </div>
        </div>

        <nav className="app-sidebar-nav" aria-label="Workspace">
          <p className="app-sidebar-section-label">Workspace</p>
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

        {appPage === "support" && (
          <section
            className="app-sidebar-chats"
            aria-label="Conversations"
          >
            <button
              type="button"
              onClick={handleNewConversation}
              disabled={loading || loadingConversation}
              className="app-sidebar-new-chat"
            >
              <Plus size={15} strokeWidth={2} aria-hidden="true" />
              New chat
            </button>

            <p className="app-sidebar-section-label app-sidebar-section-label--chats">
              Recent chats
            </p>
            <div className="app-sidebar-history-scroll">
              <ChatHistoryList
                conversations={chatHistory}
                activeConversationId={conversationId}
                loading={historyLoading}
                disabled={loading || loadingConversation}
                onSelect={handleSelectHistory}
                onDelete={handleDeleteHistory}
              />
            </div>
          </section>
        )}

        {appPage !== "support" && (
          <div className="min-h-0 flex-1" aria-hidden="true" />
        )}

        <div className="app-sidebar-account">
          <span className="app-sidebar-account-icon" aria-hidden="true">
            <UserRound size={16} strokeWidth={1.8} />
          </span>
          <div className="min-w-0">
            <span className="app-sidebar-account-label">Account Name</span>
            <span className="app-sidebar-account-name">{displayName}</span>
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

                {hasConversation && snapshot && (
                  <div className="shrink-0 px-4 pb-2">
                    <ChatAccountGlance snapshot={snapshot} />
                  </div>
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
                    disabled={assistantReplyInFlight}
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

      <ConfirmDialog
        open={deletePending != null}
        title="Delete this chat?"
        description={
          deletePending
            ? `This removes "${deletePending.title}" for ${deletePending.customer_name}. This cannot be undone.`
            : ""
        }
        confirmLabel="Delete chat"
        cancelLabel="Keep chat"
        confirmTone="danger"
        loading={deletingConversation}
        onConfirm={() => {
          void handleConfirmDeleteHistory();
        }}
        onCancel={handleCancelDeleteHistory}
      />
    </div>
  );
}
