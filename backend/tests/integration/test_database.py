from fastapi.testclient import TestClient

from app.api.routes.chat import get_chat_service
from app.main import app
from app.models.api import ChatResponse


class FakeChatService:
    def process_message(
        self,
        *,
        db,
        customer,
        message,
    ):
        return ChatResponse(
            message=f"received: {message}",
            status="VERIFIED",
            source="sqlite.customers",
        )


def test_chat_api_requires_customer_context():
    app.dependency_overrides[
        get_chat_service
    ] = lambda: FakeChatService()

    try:
        client = TestClient(app)

        response = client.post(
            "/api/chat",
            json={
                "message": "What plan am I on?"
            },
        )

        assert response.status_code == 401

    finally:
        app.dependency_overrides.clear()


def test_chat_api_uses_backend_customer_context():
    app.dependency_overrides[
        get_chat_service
    ] = lambda: FakeChatService()

    try:
        client = TestClient(app)

        response = client.post(
            "/api/chat",
            headers={
                "X-Customer-ID": "CUST001"
            },
            json={
                "message": "What plan am I on?"
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "VERIFIED"
        assert (
            response.json()["message"]
            == "received: What plan am I on?"
        )

    finally:
        app.dependency_overrides.clear()