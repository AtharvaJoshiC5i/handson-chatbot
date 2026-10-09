from types import SimpleNamespace

from app.llm.client import GroqLLMClient
from app.llm.prompts import build_response_system_prompt
from app.models.domain import TruthStatus
from app.services.chat_service import ChatService
from app.truth.result import TruthResult
from app.truth.sources import DATABASE_SOURCE


def test_generate_response_sends_only_backend_output_to_llm() -> None:
	class FakeCompletions:
		request: dict[str, object] | None = None

		def create(self, **kwargs: object) -> SimpleNamespace:
			self.request = kwargs
			return SimpleNamespace(
				choices=[
					SimpleNamespace(
						message=SimpleNamespace(
							content="Your plan is active."
						)
					)
				]
			)

	completions = FakeCompletions()
	client = GroqLLMClient.__new__(GroqLLMClient)
	client._client = SimpleNamespace(
		chat=SimpleNamespace(
			completions=completions
		)
	)
	client._model = "test-model"
	client._timeout = 1
	client._settings = SimpleNamespace(
		response_max_tokens_light=192,
		response_max_tokens_full=384,
	)

	answer = client.generate_response(
		"Your plan is currently active."
	)

	assert answer == "Your plan is active."
	assert completions.request is not None
	assert completions.request["messages"] == [
		{
			"role": "system",
			"content": build_response_system_prompt(),
		},
		{
			"role": "user",
			"content": "Your plan is currently active.",
		},
	]


def test_chat_service_uses_llm_answer_for_verified_and_clarification_results() -> None:
	class FakeLLMClient:
		received: list[str]

		def __init__(self) -> None:
			self.received = []

		def generate_response(
			self,
			backend_output: str,
			*,
			max_tokens: int | None = None,
			narrative_profile: str = "default",
		) -> str:
			self.received.append(backend_output)
			return f"Personalized answer: {backend_output}"

	client = FakeLLMClient()
	service = ChatService(client)
	results = [
		TruthResult(
			status=TruthStatus.VERIFIED,
			data={"result_type": "UNMAPPED"},
			source=DATABASE_SOURCE,
			message="Your plan is active.",
		),
		TruthResult(
			status=TruthStatus.AMBIGUOUS,
			message="Which bill would you like me to check?",
		),
	]

	responses = [
		service._build_chat_response(
			truth_result=result,
			options=[],
		)
		for result in results
	]

	assert client.received == [
		"Your plan is active.",
	]
	assert [response.message for response in responses] == [
		"Personalized answer: Your plan is active.",
		"Which bill would you like me to check?",
	]
	assert [response.status for response in responses] == [
		"VERIFIED",
		"AMBIGUOUS",
	]


def test_generate_response_stream_yields_text_deltas() -> None:
	class FakeCompletions:
		request: dict[str, object] | None = None

		def create(self, **kwargs: object) -> list[SimpleNamespace]:
			self.request = kwargs
			return [
				SimpleNamespace(
					choices=[
						SimpleNamespace(
							delta=SimpleNamespace(content="Your plan ")
						)
					]
				),
				SimpleNamespace(
					choices=[
						SimpleNamespace(
							delta=SimpleNamespace(content="is active.")
						)
					]
				),
			]

	completions = FakeCompletions()
	client = GroqLLMClient.__new__(GroqLLMClient)
	client._client = SimpleNamespace(
		chat=SimpleNamespace(
			completions=completions
		)
	)
	client._model = "test-model"
	client._timeout = 1
	client._settings = SimpleNamespace(
		response_max_tokens_light=192,
		response_max_tokens_full=384,
	)

	assert list(
		client.generate_response_stream(
			"Plan: active.",
			max_tokens=192,
		),
	) == [
		"Your plan ",
		"is active.",
	]
	assert completions.request is not None
	assert completions.request["stream"] is True
