import { useState } from "react";

import {
  Check,
  Copy,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { ChatMessage } from "../types/chat";

import { AnswerTrustFooter } from "./AnswerTrustFooter";
import { RichOptionCard } from "./RichOptionCard";
import { StructuredPresentation } from "./StructuredPresentation";
import { SuggestedFollowUps } from "./SuggestedFollowUps";
import { suggestedFollowUps } from "../utils/followUps";

interface MessageBubbleProps {
  message: ChatMessage;
  showFollowUps?: boolean;
  userMessageForFollowUps?: string;
  onOptionSelect?: (message: string) => void;
  optionsDisabled?: boolean;
}

function shouldShowNarrativeLead(
  message: ChatMessage,
): boolean {
  if (!message.content.trim()) {
    return false;
  }

  if (!message.presentation) {
    return true;
  }

  if (message.status !== "VERIFIED") {
    return true;
  }

  return false;
}

function formatTime(date: Date) {
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function AssistantMarkdown({
  content,
}: {
  content: string;
}) {
  return (
    <div className="max-w-none text-[14px] leading-7 text-[#304239]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="mb-3 mt-6 text-[21px] font-semibold leading-7 text-[#20392d] first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-2 mt-5 text-[17px] font-semibold leading-6 text-[#20392d] first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-2 mt-4 text-[14px] font-semibold leading-6 text-[#294335]">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="mb-3 last:mb-0">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="mb-4 ml-1 list-disc space-y-1.5 pl-5 marker:text-[#64836d]">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-4 ml-1 list-decimal space-y-1.5 pl-5 marker:font-medium marker:text-[#64836d]">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="pl-1 leading-7">{children}</li>
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="font-medium text-[#28624c] underline decoration-[#afc5b3] underline-offset-2 hover:text-[#173c32]"
            >
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className="my-4 border-l-2 border-[#9ab19e] pl-4 text-[#64756a]">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="my-5 border-[#e3eae4]" />,
          pre: ({ children }) => (
            <pre className="my-4 overflow-x-auto rounded-lg border border-[#dfe7e0] bg-[#f5f8f5] p-4 text-[12px] leading-6 text-[#284033]">
              {children}
            </pre>
          ),
          code: ({ children, className }) => (
            <code
              className={
                className
                  ? "font-mono text-[12px] text-inherit"
                  : "rounded bg-[#edf3ee] px-1.5 py-0.5 font-mono text-[12px] text-[#315642]"
              }
            >
              {children}
            </code>
          ),
          table: ({ children }) => (
            <div className="my-4 overflow-x-auto rounded-lg border border-[#dfe7e0]">
              <table className="w-full border-collapse text-left text-[12px]">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-[#f2f6f2] text-[#41594a]">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="whitespace-nowrap border-b border-[#e1e9e2] px-3 py-2.5 font-semibold">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border-b border-[#edf1ed] px-3 py-2.5 align-top last:border-b-0">
              {children}
            </td>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-[#223a2e]">{children}</strong>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export function MessageBubble({
  message,
  showFollowUps = false,
  userMessageForFollowUps = "",
  onOptionSelect,
  optionsDisabled = false,
}: MessageBubbleProps) {
  const [
    copied,
    setCopied,
  ] = useState(
    false,
  );

  const isUser =
    message.role === "user";

  const showNarrativeLead = shouldShowNarrativeLead(
    message,
  );

  const followUps =
    showFollowUps
    && !message.isStreaming
    && message.status === "VERIFIED"
      ? suggestedFollowUps(
          message.presentation,
          userMessageForFollowUps,
        )
      : [];

  const handleCopy =
    async () => {
      try {
        await navigator.clipboard.writeText(
          message.content,
        );

        setCopied(
          true,
        );

        window.setTimeout(
          () => {
            setCopied(
              false,
            );
          },
          1600,
        );
      } catch {
        setCopied(
          false,
        );
      }
    };

  if (isUser) {
    return (
      <div className="group flex w-full justify-end">
        <div className="max-w-[88%] sm:max-w-[76%]">
          <div className="rounded-2xl rounded-br-md border border-[var(--color-line)] bg-white px-4 py-2.5 text-[13px] leading-relaxed text-[var(--color-ink)] shadow-sm">
            <p className="whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </div>

          <div
            className={[
              "mt-1 flex h-6 items-center justify-end gap-2",
              "opacity-100 transition-opacity duration-150 sm:opacity-0",
              "sm:group-hover:opacity-100",
              "sm:group-focus-within:opacity-100",
            ].join(" ")}
          >
            <span className="text-[10px] tabular-nums text-[#85938a]">
              {formatTime(
                message.createdAt,
              )}
            </span>

            <button
              type="button"
              onClick={
                handleCopy
              }
              aria-label={
                copied
                  ? "Message copied"
                  : "Copy message"
              }
              title={
                copied
                  ? "Copied"
                  : "Copy"
              }
              className={[
                "flex h-6 w-6 items-center justify-center rounded-md",
                "text-[#718077]",
                "transition-colors duration-150",
                "hover:bg-[#e3ebe4]",
                "hover:text-[#244537]",
                "focus-visible:outline-none",
                "focus-visible:ring-2",
                "focus-visible:ring-[#6d9279]",
              ].join(" ")}
            >
              {copied ? (
                <Check
                  size={13}
                  strokeWidth={2}
                  aria-hidden="true"
                />
              ) : (
                <Copy
                  size={13}
                  strokeWidth={1.8}
                  aria-hidden="true"
                />
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="group w-full min-w-0">
      {showNarrativeLead ? (
        <AssistantMarkdown content={message.content} />
      ) : message.isStreaming ? (
        <div className="flex h-7 items-center gap-1.5" role="status" aria-label="Response is being generated">
          <span className="size-1.5 animate-pulse rounded-full bg-[#8da391]" />
          <span className="size-1.5 animate-pulse rounded-full bg-[#8da391] [animation-delay:120ms]" />
          <span className="size-1.5 animate-pulse rounded-full bg-[#8da391] [animation-delay:240ms]" />
        </div>
      ) : null}

      {message.isStreaming && message.content && (
        <span
          className="ml-1 inline-block h-[1.05em] w-[2px] translate-y-[2px] animate-pulse bg-[#5c8066]"
          aria-hidden="true"
        />
      )}

      {message.presentation && (
        <div className="mt-4 min-w-0">
          <StructuredPresentation
            presentation={message.presentation}
            onEntitySelect={onOptionSelect}
          />
        </div>
      )}

      {!message.isStreaming && (
        <AnswerTrustFooter
          status={message.status}
          source={message.source}
        />
      )}

      {followUps.length > 0 && (
        <SuggestedFollowUps
          suggestions={followUps}
          disabled={optionsDisabled}
          onSelect={(text) => onOptionSelect?.(text)}
        />
      )}

      {message.options && message.options.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {message.options.map((option) => (
            <RichOptionCard
              key={option.message}
              option={option}
              disabled={optionsDisabled}
              onSelect={(text) => onOptionSelect?.(text)}
            />
          ))}
        </div>
      )}

      <div
        className={[
          "mt-2 flex h-7 items-center gap-1",
          "opacity-100 transition-opacity duration-150 sm:opacity-0",
          "sm:group-hover:opacity-100 sm:group-focus-within:opacity-100",
        ].join(" ")}
      >
        <span className="mr-1 text-[10px] tabular-nums text-[#96a198]">
          {formatTime(message.createdAt)}
        </span>
        {message.content && (
          <button
            type="button"
            onClick={handleCopy}
            aria-label={copied ? "Response copied" : "Copy response"}
            title={copied ? "Copied" : "Copy"}
            className="flex size-7 items-center justify-center rounded-md text-[#7d8b81] transition-colors hover:bg-[#e9efea] hover:text-[#294737] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6d9279]"
          >
            {copied ? (
              <Check size={14} strokeWidth={2} aria-hidden="true" />
            ) : (
              <Copy size={14} strokeWidth={1.8} aria-hidden="true" />
            )}
          </button>
        )}
      </div>
    </div>
  );
}