from app.models.api import KeyValuePresentation
from app.models.domain import TruthStatus
from app.services.response_narrative_policy import (
    should_skip_response_rewrite,
)


def test_skip_rewrite_for_verified_with_presentation_in_auto_mode() -> None:
    presentation = KeyValuePresentation(
        type="key_value",
        items=[],
    )

    assert should_skip_response_rewrite(
        TruthStatus.VERIFIED,
        presentation,
        "auto",
    )


def test_rewrite_allowed_for_verified_without_presentation() -> None:
    assert not should_skip_response_rewrite(
        TruthStatus.VERIFIED,
        None,
        "auto",
    )


def test_skip_rewrite_for_clarification_status() -> None:
    assert should_skip_response_rewrite(
        TruthStatus.AMBIGUOUS,
        None,
        "full",
    )
