from app.database.connection import create_connection
from app.intent.router import IntentRouter
from app.models.api import ChatResponse
from app.models.domain import (
    CustomerContext,
    Intent,
    TimeRange,
    TruthStatus,
)
from app.models.llm import (
    IntentParameters,
    LLMIntentResponse,
)
from app.services.chat_service import ChatService
from app.services.response_service import ResponseService


class FakeLLMClient:
    """Deterministic LLM replacement for integration tests."""

    def __init__(
        self,
        response: LLMIntentResponse,
    ):
        self.response = response

    def extract_intent(
        self,
        user_message: str,
    ) -> LLMIntentResponse:
        return self.response


def run_chat(
    intent: Intent,
    *,
    parameters: IntentParameters | None = None,
    customer_id: str = "CUST001",
) -> ChatResponse:
    db = create_connection()

    try:
        client = FakeLLMClient(
            LLMIntentResponse(
                intent=intent,
                parameters=(
                    parameters
                    or IntentParameters()
                ),
            )
        )

        service = ChatService(
            llm_client=client,
            intent_router=IntentRouter(),
            response_service=ResponseService(),
        )

        return service.process_message(
            db=db,
            customer=CustomerContext(
                customer_id=customer_id
            ),
            message="test message",
        )

    finally:
        db.close()


def test_all_supported_phase_one_intents_execute():
    cases = [
        (
            Intent.GET_CURRENT_PLAN,
            IntentParameters(),
        ),
        (
            Intent.GET_ACCOUNT_STATUS,
            IntentParameters(),
        ),
        (
            Intent.GET_PLAN_RENEWAL,
            IntentParameters(),
        ),
        (
            Intent.GET_DATA_USAGE,
            IntentParameters(
                time_range=TimeRange.CURRENT_MONTH
            ),
        ),
        (
            Intent.GET_VOICE_USAGE,
            IntentParameters(
                time_range=TimeRange.CURRENT_MONTH
            ),
        ),
        (
            Intent.GET_CURRENT_BILL,
            IntentParameters(),
        ),
        (
            Intent.GET_BILL_HISTORY,
            IntentParameters(limit=2),
        ),
        (
            Intent.GET_TOTAL_SPENDING,
            IntentParameters(),
        ),
        (
            Intent.GET_BILL_COMPARISON,
            IntentParameters(),
        ),
        (
            Intent.GET_PAYMENT_STATUS,
            IntentParameters(),
        ),
        (
            Intent.GET_PAYMENT_HISTORY,
            IntentParameters(limit=2),
        ),
        (
            Intent.GET_SUPPORT_TICKETS,
            IntentParameters(),
        ),
        (
            Intent.GET_DEVICE_INFORMATION,
            IntentParameters(),
        ),
        (
            Intent.UNSUPPORTED,
            IntentParameters(),
        ),
    ]

    for intent, parameters in cases:
        response = run_chat(
            intent,
            parameters=parameters,
        )

        assert response.status in {
            TruthStatus.VERIFIED.value,
            TruthStatus.UNSUPPORTED.value,
        }

        assert response.message


def test_bill_comparison_without_explicit_ids_uses_latest_two_bills():
    response = run_chat(
        Intent.GET_BILL_COMPARISON,
        customer_id="CUST005",
    )

    assert response.status == TruthStatus.VERIFIED.value
    assert "BILL009" in response.message
    assert "BILL010" in response.message


def test_bill_comparison_with_explicit_ids():
    response = run_chat(
        Intent.GET_BILL_COMPARISON,
        parameters=IntentParameters(
            current_bill_id="BILL009",
            previous_bill_id="BILL010",
        ),
        customer_id="CUST005",
    )

    assert response.status == TruthStatus.VERIFIED.value
    assert "BILL009" in response.message
    assert "BILL010" in response.message