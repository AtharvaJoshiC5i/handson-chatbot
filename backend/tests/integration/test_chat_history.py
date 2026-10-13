from uuid import uuid4

from app.database.connection import create_connection
from app.models.api import ChatOption
from app.models.domain import CustomerContext
from app.services.chat_history_service import ChatHistoryService
from app.services.chat_service import ChatService


class StaticLLMClient:
    def extract_intent(self, user_message: str):
        from app.intent.definitions import Intent
        from app.models.llm import IntentParameters, LLMIntentResponse

        return LLMIntentResponse(
            intent=Intent.GET_ACCOUNT_STATUS,
            parameters=IntentParameters(),
        )

    def generate_response(self, backend_output: str, **kwargs) -> str:
        return backend_output


def test_chat_history_persists_exchange_and_loads_messages():
    db = create_connection()
    history = ChatHistoryService()
    conversation_id = uuid4().hex

    try:
        service = ChatService(llm_client=StaticLLMClient())
        response = service.respond(
            db=db,
            customer=CustomerContext(customer_id="CUST001"),
            user_message="What is my account status?",
            conversation_id=conversation_id,
        )

        assert response.status == "VERIFIED"

        summaries = history.list_for_customer(db, "CUST001")
        assert any(
            row["conversation_id"] == conversation_id for row in summaries
        )

        messages = history.load_messages(
            db,
            conversation_id=conversation_id,
            customer_id="CUST001",
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "What is my account status?"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"]

        history.record_exchange(
            db,
            conversation_id=uuid4().hex,
            customer_id="CUST002",
            user_message="Latest bill please",
            assistant_message="Your latest bill is ready.",
            status="VERIFIED",
            source="test",
            presentation=None,
            options=[ChatOption(label="Pay", message="Pay my bill")],
        )

        all_rows = history.list_all(db)
        customer_names = {
            row["customer_id"]: row["customer_name"] for row in all_rows
        }
        assert customer_names.get("CUST002") == "Diya Mehta"

    finally:
        db.close()
