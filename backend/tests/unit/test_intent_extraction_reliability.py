from types import SimpleNamespace

from app.llm.client import (
    GroqLLMClient,
    classify_deterministic_request,
)
from app.models.domain import Intent, TruthStatus, CustomerContext
from app.models.llm import IntentParameters, LLMIntentResponse
from app.services.chat_service import ChatService
from app.truth.result import TruthResult
from app.truth.sources import DATABASE_SOURCE
from app.utils.errors import LLMError


class FakeCompletions:
    def __init__(self, contents: list[str]) -> None:
        self.contents = contents
        self.requests: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.requests.append(kwargs)
        content = self.contents.pop(0)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content)
                )
            ]
        )


def _client(contents: list[str]) -> tuple[GroqLLMClient, FakeCompletions]:
    completions = FakeCompletions(contents)
    client = GroqLLMClient.__new__(GroqLLMClient)
    client._client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )
    client._model = "test-model"
    client._timeout = 1
    return client, completions


def test_intent_extraction_repairs_malformed_schema_output() -> None:
    client, completions = _client(
        [
            "not valid json",
            '{"intent":"GET_DATA_USAGE","parameters":{"month":9}}',
        ]
    )

    result = client.extract_intent(
        "Can you retrieve my records for a particular month?"
    )

    assert result.intent == Intent.GET_DATA_USAGE
    assert result.parameters.month == 9
    assert len(completions.requests) == 2
    assert "REGISTERED BACKEND CAPABILITIES" in completions.requests[0]["messages"][0]["content"]
    retry_messages = completions.requests[1]["messages"]
    assert isinstance(retry_messages, list)
    assert retry_messages[-1]["role"] == "user"
    assert "corrected JSON" in retry_messages[-1]["content"]


def test_intent_extraction_clarifies_after_repeated_invalid_output() -> None:
    client, completions = _client(
        ["not valid json", "still not valid json"]
    )

    result = client.extract_intent(
        "Can you retrieve my records for a particular month?"
    )

    assert result.intent == Intent.UNSUPPORTED
    assert result.clarification is not None
    assert "rephrase" in result.clarification
    assert len(completions.requests) == 2


def test_usage_graph_clarification_preserves_month_window() -> None:
    result = classify_deterministic_request(
        "show me my usage accross a graph for the last 4 months",
    )

    assert result is not None
    assert result.intent == Intent.UNSUPPORTED
    assert result.clarification is not None
    assert "4 months" in result.clarification
    assert len(result.options) == 3
    assert result.options[0].message == (
        "Show my data usage for the last 4 months."
    )
    assert result.options[1].message == (
        "Show my voice usage for the last 4 months."
    )
    assert result.options[2].message == (
        "Show my SMS usage for the last 4 months."
    )


def test_usage_graph_with_data_type_routes_to_history() -> None:
    result = classify_deterministic_request(
        "Show my data usage on a chart for the last 4 months",
    )

    assert result is not None
    assert result.intent == Intent.GET_USAGE_HISTORY
    assert result.parameters.usage_type.value == "DATA"
    assert result.parameters.month_count == 4


def test_unpaid_bills_routes_to_filter_not_payment_status() -> None:
    result = classify_deterministic_request(
        "do I have any previously unpaid bills",
    )

    assert result is not None
    assert result.intent == Intent.FILTER_BILLS
    assert result.parameters.status_filter.value == "UNPAID"


def test_open_cases_routes_to_support_tickets() -> None:
    result = classify_deterministic_request(
        "Show my open cases.",
    )

    assert result is not None
    assert result.intent == Intent.GET_SUPPORT_TICKETS
    assert result.parameters.ticket_status.value == "OPEN"


def test_router_question_filters_device_type() -> None:
    result = classify_deterministic_request(
        "Do I have a router registered?",
    )

    assert result is not None
    assert result.intent == Intent.FILTER_DEVICES
    assert result.parameters.device_type.value == "ROUTER"


def test_latest_bill_compare_strips_hallucinated_month_params() -> None:
    from app.llm.client import _normalize_extracted_intent
    from app.models.llm import IntentParameters

    normalized = _normalize_extracted_intent(
        LLMIntentResponse(
            intent=Intent.GET_BILL_COMPARISON,
            parameters=IntentParameters(
                month=1,
                year=2026,
                comparison_month=12,
                comparison_year=2025,
            ),
        ),
        "Compare my latest bill with the previous one.",
    )

    assert normalized.parameters.month is None
    assert normalized.parameters.comparison_month is None


def test_plan_id_compare_routes_deterministically() -> None:
    result = classify_deterministic_request(
        "Compare PLAN001 and PLAN003",
    )

    assert result is not None
    assert result.intent == Intent.GET_PLAN_COMPARISON
    assert result.parameters.plan_id == "PLAN001"
    assert result.parameters.comparison_plan_id == "PLAN003"


def test_named_month_usage_compare_routes_to_comparison() -> None:
    result = classify_deterministic_request(
        "compare June data usage with August",
    )

    assert result is not None
    assert result.intent == Intent.GET_USAGE_COMPARISON
    assert result.parameters.usage_type.value == "DATA"
    assert result.parameters.month == 8
    assert result.parameters.comparison_month == 6


def test_payment_profile_phrases_classify_deterministically() -> None:
    cases = [
        (
            "Do I have any account credits?",
            Intent.GET_ACCOUNT_CREDITS,
        ),
        (
            "Is autopay enabled?",
            Intent.GET_PAYMENT_PROFILE,
        ),
    ]
    for question, expected_intent in cases:
        result = classify_deterministic_request(question)
        assert result is not None
        assert result.intent == expected_intent


def test_named_month_usage_questions_are_classified_without_llm() -> None:
    examples = [
        ("Give me my data usage for September", 9, None),
        ("How much data did I use in August 2025?", 8, 2025),
        ("Show my July data usage", 7, None),
        ("Give me my voice usage for November", 11, None),
    ]

    for question, expected_month, expected_year in examples:
        result = classify_deterministic_request(question)

        assert result is not None
        assert result.intent in {Intent.GET_DATA_USAGE, Intent.GET_VOICE_USAGE}
        assert result.parameters.month == expected_month
        assert result.parameters.year == expected_year


def test_chat_response_falls_back_to_backend_text_if_final_llm_fails() -> None:
    class FailingResponseClient:
        def generate_response(
            self,
            _backend_output: str,
            *,
            max_tokens: int | None = None,
        ) -> str:
            raise LLMError("temporary prose-generation failure")

    service = ChatService(FailingResponseClient())
    result = TruthResult(
        status=TruthStatus.VERIFIED,
        data={"result_type": "UNMAPPED"},
        source=DATABASE_SOURCE,
        message="Your account is active.",
    )

    response = service._build_chat_response(
        truth_result=result,
        options=[],
    )

    assert response.message == "Your account is active."
    assert response.status == "VERIFIED"


def test_stream_falls_back_if_final_llm_fails_before_first_delta() -> None:
    class FailingStreamClient:
        def generate_response_stream(
            self,
            _backend_output: str,
            *,
            max_tokens: int | None = None,
        ):
            def failed_stream():
                raise LLMError("temporary stream failure")
                yield ""

            return failed_stream()

    service = ChatService(FailingStreamClient())
    result = TruthResult(
        status=TruthStatus.VERIFIED,
        data={"result_type": "UNMAPPED"},
        source=DATABASE_SOURCE,
        message="Your account is active.",
    )
    service._process_turn = lambda **_kwargs: (
        result,
        [],
        None,
    )

    _, text_stream = service.respond_stream(
        db=None,
        customer=CustomerContext(customer_id="CUST001"),
        user_message="Is my account active?",
    )

    assert list(text_stream) == ["Your account is active."]