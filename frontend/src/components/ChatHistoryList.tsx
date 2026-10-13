import { MessageSquare, Trash2 } from "lucide-react";

import type { ChatConversationSummary } from "../types/chat";
import { formatRelativeTime } from "../utils/formatRelativeTime";

interface ChatHistoryListProps {
  conversations: ChatConversationSummary[];
  activeConversationId: string | null;
  loading?: boolean;
  disabled?: boolean;
  onSelect: (conversation: ChatConversationSummary) => void;
  onDelete: (conversation: ChatConversationSummary) => void;
}

export function ChatHistoryList({
  conversations,
  activeConversationId,
  loading = false,
  disabled = false,
  onSelect,
  onDelete,
}: ChatHistoryListProps) {
  if (loading && conversations.length === 0) {
    return (
      <p className="app-sidebar-empty">Loading conversations…</p>
    );
  }

  if (conversations.length === 0) {
    return (
      <p className="app-sidebar-empty">
        No saved chats yet. Start a new conversation to build history.
      </p>
    );
  }

  return (
    <ul className="chat-history-list" aria-label="Chat history">
      {conversations.map((conversation) => {
        const active = conversation.conversation_id === activeConversationId;

        return (
          <li
            key={conversation.conversation_id}
            className={[
              "chat-history-row",
              active ? "chat-history-row--active" : "",
            ].join(" ")}
          >
            <button
              type="button"
              disabled={disabled}
              onClick={() => onSelect(conversation)}
              className="chat-history-item"
            >
              <span className="chat-history-item-icon" aria-hidden="true">
                <MessageSquare size={14} strokeWidth={1.75} />
              </span>
              <span className="chat-history-item-body">
                <span className="chat-history-item-title">
                  {conversation.title}
                </span>
                <span className="chat-history-item-meta">
                  <span className="chat-history-item-customer">
                    {conversation.customer_name}
                  </span>
                  <span className="chat-history-item-sep" aria-hidden="true">
                    ·
                  </span>
                  <span>
                    {formatRelativeTime(conversation.updated_at)}
                  </span>
                </span>
              </span>
            </button>
            <button
              type="button"
              disabled={disabled}
              className="chat-history-delete"
              aria-label={`Delete chat: ${conversation.title}`}
              title="Delete chat"
              onClick={(event) => {
                event.stopPropagation();
                onDelete(conversation);
              }}
            >
              <Trash2 size={13} strokeWidth={1.85} aria-hidden="true" />
            </button>
          </li>
        );
      })}
    </ul>
  );
}
