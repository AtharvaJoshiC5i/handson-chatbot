from types import SimpleNamespace

from app.llm.client import (
    GroqLLMClient,
    classify_deterministic_request,
)
from app.models.domain import Intent, TruthStatus, CustomerContext
from app.models.llm import IntentParameters
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