from __future__ import annotations

import json
import sqlite3

from fastapi.testclient import TestClient

from app.api.routes import chat as chat_route
from app.database.seed import seed_database
from app.main import app
from app.models.domain import Intent
from app.models.llm import IntentParameters, LLMIntentResponse


class FakeStreamingClient:
    backend_output: str | None = None

    def extract_intent(self, user_message: str) -> LLMIntentResponse:
        return LLMIntentResponse(
            intent=Intent.GET_ACCOUNT_STATUS,
            parameters=IntentParameters(),
        )

    def generate_response_stream(
        self,
        backend_output: str,
        *,
        max_tokens: int | None = None,
    ):
        self.backend_output = backend_output
        yield "Your account "
        yield "is active."


def test_chat_stream_sends_metadata_then_generated_text_deltas(
    monkeypatch,
) -> None:
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    seed_database(db, reset=True)

    fake_client = FakeStreamingClient()
    monkeypatch.setattr(
        chat_route,
        "GroqLLMClient",
        lambda _settings: fake_client,
    )
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[chat_route.get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/chat/stream",
                headers={"X-Customer-ID": "CUST001"},
                json={
                    "message": "Is my account active?",
                    "conversation_id": "stream-test-account-status",
                },
            )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        events = response.text.replace("\r\n", "\n").strip().split("\n\n")
        assert [event.splitlines()[0] for event in events] == [
            "event: metadata",
            "event: delta",
            "event: delta",
            "event: done",
        ]

        metadata_data = next(
            line.removeprefix("data: ")
            for line in events[0].splitlines()
            if line.startswith("data: ")
        )
        metadata = json.loads(metadata_data)
        assert metadata["status"] == "VERIFIED"
        assert metadata["message"] == ""
        assert fake_client.backend_output == "Your account status is active."

        deltas = [
            json.loads(
                next(
                    line.removeprefix("data: ")
                    for line in event.splitlines()
                    if line.startswith("data: ")
                )
            )["text"]
            for event in events
            if event.startswith("event: delta")
        ]
        assert "".join(deltas) == "Your account is active."
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        db.close()


def test_customer_profile_returns_name_from_selected_account() -> None:
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    seed_database(db, reset=True)
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[chat_route.get_db] = lambda: db

    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/chat/profile",
                headers={"X-Customer-ID": "CUST001"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Aarav Sharma"
        assert body["account_status"] == "ACTIVE"
        assert "phone_masked" in body
        assert "city" in body
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        db.close()