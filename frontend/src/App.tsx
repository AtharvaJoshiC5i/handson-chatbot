import { useRef, useState } from "react";

import {
  ArrowUpRight,
  ChartNoAxesColumnIncreasing,
  CircleAlert,
  CircleHelp,
  CreditCard,
  Headphones,
  MessagesSquare,
  Plus,
  ReceiptText,
  Signal,
  UserRound,
} from "lucide-react";

import { ChatWindow } from "./components/ChatWindow";
import { CustomerSelector } from "./components/CustomerSelector";
import { MessageInput } from "./components/MessageInput";
import {
  resetConversationContext,
  streamChatMessage,
} from "./services/api";

import type { ChatMessage } from "./types/chat";

const starterPrompts = [
  {
    title: "Your plan",
    description: "See the plan and features on your account",
    prompt: "Check my current plan",
    icon: CreditCard,
    tone: "bg-[#e8f1eb] text-[#28624c]",
  },
  {
    title: "Data & usage",
    description: "Review your usage for this cycle",
    prompt: "Review my data usage",
    icon: ChartNoAxesColumnIncreasing,
    tone: "bg-[#eff1e8] text-[#586c35]",
  },
  {
    title: "Latest bill",
    description: "Find a charge or check your bill details",
    prompt: "Show my latest bill",
    icon: ReceiptText,
    tone: "bg-[#f5eee5] text-[#95652d]",
  },
  {
    title: "Payment support",
    description: "Get help with a payment or payment method",
    prompt: "Help with a payment",
    icon: CircleHelp,
    tone: "bg-[#eaf0f1] text-[#426578]",
  },
];

function createMessageId(): string {
  return `${Date.now()}-${Math.random()
    .toString(36)
    .slice(2)}`;
}

function createConversationId(): string {
  return globalThis.crypto?.randomUUID?.()
    ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function App() {
  const [
    customerId,
    setCustomerId,
  ] = useState(
    "CUST001",
  );

  const [
    conversationId,
    setConversationId,
  ] = useState(
    createConversationId,
  );

  const [
    messages,
    setMessages,
  ] = useState<
    ChatMessage[]
  >([]);

  const [
    loading,
    setLoading,
  ] = useState(
    false,
  );

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const hasConversation =
    messages.length > 0;

  const handleCustomerChange = (
    nextCustomerId: string,
  ) => {
    void resetConversationContext(
      customerId,
      conversationId,
    );

    setCustomerId(
      nextCustomerId,
    );

    setConversationId(
      createConversationId(),
    );
    setMessages([]);
    setError(null);
  };

  const handleNewConversation = () => {
    if (loading) {
      return;
    }

    void resetConversationContext(
      customerId,
      conversationId,
    );

    setConversationId(
      createConversationId(),
    );
    setMessages([]);
    setError(null);
  };

  const handleSend = async (
    messageText: string,
  ) => {
    const trimmedMessage =
      messageText.trim();

    if (
      !trimmedMessage ||
      loading
    ) {
      return;
    }

    setError(null);

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content: trimmedMessage,
      createdAt: new Date(),
    };
    const assistantMessageId = createMessageId();
    const abortController = new AbortController();
    let streamedText = "";
    abortControllerRef.current = abortController;

    setMessages(
      (current) => [
        ...current,
        userMessage,
        {
          id: assistantMessageId,
          role: "assistant",
          content: "",
          createdAt: new Date(),
          isStreaming: true,
        },
      ],
    );

    setLoading(true);

    try {
      await streamChatMessage(
          customerId,
          trimmedMessage,
          conversationId,
          {
            onMetadata: (response) => {
              setMessages((current) =>
                current.map((message) =>
                  message.id === assistantMessageId
                    ? {
                        ...message,
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
    } catch (
      requestError
    ) {
      const wasAborted = abortController.signal.aborted;
      const errorMessage =
        requestError instanceof
        Error
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

      setLoading(
        false,
      );
    }
  };

  const handleStop = () => {
    abortControllerRef.current?.abort();
  };

  return (
    <div className="app-shell flex h-dvh min-h-0 overflow-hidden font-sans text-[#23352e]">
      {/* Sidebar */}
      <aside className="hidden w-[236px] shrink-0 flex-col border-r border-[#e0e7e1] bg-[#f3f6f3] text-[#26392f] lg:flex">
        <div className="flex h-[72px] items-center gap-3 border-b border-[#e3e9e4] px-5">
          <span className="grid size-9 place-items-center rounded-md bg-[#e2ece4] text-[#285647]">
            <Signal size={18} strokeWidth={1.9} aria-hidden="true" />
          </span>
          <div>
            <span className="block text-[16px] font-semibold leading-5 text-[#20372c]">
              NexaTel
            </span>
            <span className="mt-0.5 block text-[10px] text-[#77877c]">
              Customer care
            </span>
          </div>
        </div>

        <div className="px-3 pt-5">
          <button
            type="button"
            onClick={
              handleNewConversation
            }
            disabled={
              loading
            }
            className={[
              "flex h-10 w-full items-center gap-2.5 rounded-md border border-transparent bg-[#1d4b3b] px-3",
              "text-[12px] font-medium text-white shadow-sm shadow-[#173c32]/10",
              "transition-colors duration-150",
              "hover:bg-[#285b47]",
              "focus-visible:outline-none",
              "focus-visible:ring-2",
              "focus-visible:ring-[#6f927a] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f3f6f3]",
              "disabled:pointer-events-none disabled:opacity-40",
            ].join(" ")}
          >
            <Plus
              size={14}
              strokeWidth={2}
              className="text-[#dbe7dc]"
              aria-hidden="true"
            />

            <span>
              New conversation
            </span>
          </button>
        </div>

        <nav
          className="px-3 pt-7"
          aria-label="Conversations"
        >
          <p className="px-3 pb-2 text-[10px] font-medium text-[#7d8c81]">
            Workspace
          </p>

          <button
            type="button"
            onClick={handleNewConversation}
            disabled={loading}
            className={[
              "flex h-10 w-full items-center gap-2.5 rounded-md border-l-2 border-[#397354] px-3",
              "bg-[#e5eee6]",
              "text-left text-[12px] font-semibold text-[#264a38]",
              "transition-colors duration-150",
              "hover:bg-[#dde9df]",
            ].join(" ")}
          >
            <MessagesSquare size={15} strokeWidth={1.8} className="shrink-0 text-[#397354]" aria-hidden="true" />

            <span className="truncate">
              Support assistant
            </span>
          </button>
        </nav>

        <div className="mt-auto border-t border-[#e3e9e4] px-4 py-4">
          <div className="flex items-center gap-3 px-2 py-1.5">
            <span className="grid size-8 shrink-0 place-items-center rounded-md bg-white text-[#52715d] ring-1 ring-[#dfe7e0]">
              <UserRound size={16} strokeWidth={1.8} aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <span className="block text-[10px] text-[#7a897f]">
                Selected account
              </span>
              <span className="mt-0.5 block truncate text-[11px] font-semibold tabular-nums text-[#2c4336]">
                {customerId}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main application */}
      <div className="flex min-h-0 min-w-0 flex-1 flex-col ">
        {/* Header */}
        <header className="flex h-[60px] shrink-0 items-center justify-between border-b border-[#e2e8e3] bg-white px-4 sm:px-7">
          <div className="flex min-w-0 items-center gap-3">
            <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-[#edf3ef] text-[#285647] lg:hidden">
              <Headphones size={18} strokeWidth={1.8} aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <span className="block truncate text-[13px] font-semibold text-[#23352e]">
                Support assistant
              </span>
              <span className="mt-0.5 block text-[10px] text-[#839087]">
                NexaTel customer care
              </span>
            </div>
          </div>

          <div
            id="customer-context"
            className="flex items-center gap-2.5"
          >
            <span className="hidden text-[10px] font-medium text-[#7e8d84] sm:block">
              ACCOUNT
            </span>

            <CustomerSelector
              customerId={
                customerId
              }
              onCustomerChange={
                handleCustomerChange
              }
              disabled={
                loading
              }
            />
          </div>
        </header>

        {/* Conversation */}
        <main
          id="conversation"
          aria-busy={
            loading
          }
          className="min-h-0 flex-1 overflow-hidden bg-[#f6f8f5]"
        >
          <div className="mx-auto flex h-full w-full max-w-[920px] flex-col">
            {!hasConversation ? (
              <div className="flex min-h-0 flex-1 flex-col justify-center overflow-y-auto px-5 pb-6 pt-8 sm:px-9 lg:px-12">
                <section className="mx-auto w-full max-w-[740px] py-6">
                  <div className="mb-6 flex items-center gap-3">
                    <span className="grid size-11 place-items-center rounded-xl bg-[#173c32] text-[#f0d69a]">
                      <Headphones size={20} strokeWidth={1.8} aria-hidden="true" />
                    </span>
                    <div>
                      <p className="text-[9px] font-semibold text-[#84938a]">
                        NEXATEL CUSTOMER CARE
                      </p>
                      <p className="mt-1 text-[11px] font-medium tabular-nums text-[#3f574b]">
                        Account {customerId}
                      </p>
                    </div>
                  </div>
                  <h1 className="max-w-[600px] text-[32px] font-semibold leading-[1.15] text-[#1c342b] sm:text-[40px]">
                    How can we help you today?
                  </h1>
                  <p className="mt-3 max-w-[500px] text-[14px] leading-6 text-[#74837a]">
                    Get clear answers about your plan, data, bills, and payments.
                  </p>

                  <div className="mt-9">
                    <p className="mb-3 text-[9px] font-semibold text-[#86938b]">
                      POPULAR TOPICS
                    </p>
                    <div
                      className="grid grid-cols-1 gap-2 sm:grid-cols-2 sm:gap-3"
                      aria-label="Suggested questions"
                    >
                      {starterPrompts.map((item) => {
                        const Icon = item.icon;

                        return (
                          <button
                            key={item.prompt}
                            type="button"
                            onClick={() => handleSend(item.prompt)}
                            disabled={loading}
                            className={[
                              "group flex min-h-[82px] items-center gap-3 rounded-md border border-[#e1e8e2] bg-white px-3.5 py-3 text-left",
                              "transition duration-150 hover:border-[#b6c9bb] hover:bg-[#fcfdfb] hover:shadow-[0_5px_16px_rgba(28,52,43,0.06)]",
                              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#41705d] focus-visible:ring-offset-2",
                              "disabled:pointer-events-none disabled:opacity-40",
                            ].join(" ")}
                          >
                            <span className={`grid size-9 shrink-0 place-items-center rounded-md ${item.tone}`}>
                              <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
                            </span>
                            <span className="min-w-0 flex-1">
                              <span className="block text-[12px] font-semibold text-[#2c3c35]">
                                {item.title}
                              </span>
                              <span className="mt-1 block text-[10px] leading-[1.5] text-[#819087]">
                                {item.description}
                              </span>
                            </span>
                            <ArrowUpRight
                              size={15}
                              strokeWidth={1.8}
                              aria-hidden="true"
                              className="shrink-0 text-[#9aa69e] transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-[#28624c]"
                            />
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </section>
              </div>
            ) : (
              <ChatWindow
                messages={
                  messages
                }
                loading={
                  loading
                }
                onOptionSelect={
                  handleSend
                }
              />
            )}

            {error && (
              <div className="shrink-0 px-4 pb-2 sm:px-6">
                <div
                  role="alert"
                  className={[
                    "flex items-start gap-2.5 rounded-md border border-[#eed5d0]",
                    "bg-[#fff8f6] px-3.5 py-3",
                    "text-[11px] leading-5 text-[#874b43]",
                  ].join(
                    " ",
                  )}
                >
                  <CircleAlert size={15} className="mt-0.5 shrink-0" aria-hidden="true" />
                  <span>{error}</span>
                </div>
              </div>
            )}

            <MessageInput
              onSend={
                handleSend
              }
              onStop={handleStop}
              disabled={
                loading
              }
            />
          </div>
        </main>
      </div>
    </div>
  );
}