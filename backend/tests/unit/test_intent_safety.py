import pytest

from app.intent.parameters import validate_allowed_parameters
from app.models.domain import Intent
from app.models.llm import LLMIntentResponse
from app.services.structured_data_service import StructuredDataService
from app.utils.errors import ValidationError


def test_router_parameter_contract_rejects_unexpected_values() -> None:
    with pytest.raises(ValidationError):
        validate_allowed_parameters(
            intent_parameters={"limit": 5},
            allowed_parameters=frozenset(),
        )


class FakeExtractor:
    def extract(self, user_message: str) -> LLMIntentResponse:
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "Do you mean your data usage or your voice usage?"
            ),
        )


def test_clarification_result_stops_before_database_routing() -> None:
    service = StructuredDataService(
        intent_extractor=FakeExtractor(),
        intent_router=object(),
    )

    _, result = service.execute(
        db=None,
        customer=None,
        user_message="How much have I used?",
    )

    assert result.status.value == "AMBIGUOUS"
    assert "data usage" in result.message