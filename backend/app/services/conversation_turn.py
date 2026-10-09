"""Immutable record of one chat turn for intent context."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConversationTurn:
    user_message: str
    intent: str
    status: str
    result_type: str | None
    domain: str | None
    facts: str

    def format_line(self, index: int) -> str:
        user = self.user_message.replace('"', "'")
        result = self.result_type or "—"
        return (
            f'Turn {index}: user="{user}" | '
            f"{self.intent} {self.status} | {result} | {self.facts}"
        )
