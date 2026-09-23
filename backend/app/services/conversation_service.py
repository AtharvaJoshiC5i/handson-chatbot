"""Lightweight conversation context for NexaTel Phase 1."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversationMessage:
    """One message in the conversation."""

    role: str
    content: str


@dataclass
class ConversationContext:
    """Ephemeral conversation context.

    Customer identity is intentionally excluded.

    Authentication comes exclusively from the backend request context.
    """

    messages: list[ConversationMessage] = field(
        default_factory=list
    )

    def add_user_message(
        self,
        content: str,
    ) -> None:
        """Add a user message."""

        self.messages.append(
            ConversationMessage(
                role="user",
                content=content,
            )
        )

    def add_assistant_message(
        self,
        content: str,
    ) -> None:
        """Add an assistant message."""

        self.messages.append(
            ConversationMessage(
                role="assistant",
                content=content,
            )
        )

    def recent_messages(
        self,
        limit: int = 10,
    ) -> list[ConversationMessage]:
        """Return the most recent messages."""

        if limit <= 0:
            return []

        return self.messages[-limit:]