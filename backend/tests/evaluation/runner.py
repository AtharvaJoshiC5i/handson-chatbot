"""Evaluation runner for the NexaTel Phase 1 system."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.database.connection import create_connection
from app.intent.router import IntentRouter
from app.models.domain import (
    CustomerContext,
    Intent,
    TruthStatus,
)
from app.models.llm import (
    IntentParameters,
    LLMIntentResponse,
)
from app.services.chat_service import ChatService
from app.services.response_service import ResponseService
from app.truth.result import TruthResult


DATASET_PATH = Path(__file__).with_name(
    "dataset.json"
)


class IntentProvider(Protocol):
    """Protocol for an intent provider used by evaluation."""

    def extract_intent(
        self,
        user_message: str,
    ) -> LLMIntentResponse:
        ...


class GroqEvaluationProvider:
    """Live Groq provider for evaluation runs."""

    def __init__(self) -> None:
        from app.config.settings import get_settings
        from app.llm.client import GroqLLMClient

        self._client = GroqLLMClient(
            get_settings()
        )

    def extract_intent(
        self,
        user_message: str,
    ) -> LLMIntentResponse:
        return self._client.extract_intent(
            user_message
        )


class FakeEvaluationProvider:
    """
    Deterministic provider for backend-only evaluation.

    This provider receives the expected structured intent from the
    evaluation case. It intentionally bypasses Groq so that backend
    routing, validation, handlers, SQLite, and response generation
    can be evaluated independently of model quality.
    """

    def __init__(
        self,
        case: dict[str, Any],
    ) -> None:
        self._case = case

    def extract_intent(
        self,
        user_message: str,
    ) -> LLMIntentResponse:
        return LLMIntentResponse(
            intent=Intent(
                self._case["expected_intent"]
            ),
            parameters=IntentParameters(
                **self._case.get(
                    "expected_parameters",
                    {},
                )
            ),
        )



class ReplayEvaluationProvider:
    """Reuse one live extraction while evaluating backend execution."""

    def __init__(
        self,
        response: LLMIntentResponse,
    ) -> None:
        self._response = response

    def extract_intent(
        self,
        user_message: str,
    ) -> LLMIntentResponse:
        return self._response


@dataclass
class EvaluationRun:
    """Complete evaluation output."""

    results: list[dict[str, Any]]

    @property
    def metrics(self):
        from .metrics import build_metrics

        return build_metrics(
            self.results
        )


def load_dataset(
    path: Path = DATASET_PATH,
) -> list[dict[str, Any]]:
    """Load and validate the evaluation dataset."""

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError(
            "Evaluation dataset must be a JSON array."
        )

    required_fields = {
        "id",
        "category",
        "customer_id",
        "question",
        "expected_intent",
        "expected_parameters",
    }

    for index, case in enumerate(dataset):
        if not isinstance(case, dict):
            raise ValueError(
                f"Dataset case {index} must be an object."
            )

        missing = required_fields - case.keys()

        if missing:
            raise ValueError(
                f"Dataset case {index} is missing: "
                f"{sorted(missing)}"
            )

        Intent(case["expected_intent"])

        if not isinstance(
            case["expected_parameters"],
            dict,
        ):
            raise ValueError(
                f"Dataset case {case['id']} has invalid "
                "expected_parameters."
            )

    return dataset


def _normalize_parameters(
    parameters: IntentParameters,
) -> dict[str, Any]:
    """Convert structured parameters into comparable JSON data."""

    result: dict[str, Any] = {}

    if parameters.time_range is not None:
        result["time_range"] = (
            parameters.time_range.value
        )

    if parameters.limit is not None:
        result["limit"] = parameters.limit

    if parameters.current_bill_id is not None:
        result["current_bill_id"] = (
            parameters.current_bill_id
        )

    if parameters.previous_bill_id is not None:
        result["previous_bill_id"] = (
            parameters.previous_bill_id
        )

    return result


def _parameters_match(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> bool:
    """
    Compare expected parameters strictly.

    The evaluator ignores missing optional parameters only when both
    sides have no value. Otherwise the values must match exactly.
    """

    return expected == actual


def _run_single_case(
    case: dict[str, Any],
    provider_factory,
) -> dict[str, Any]:
    """Execute one evaluation case."""

    started = time.perf_counter()

    result: dict[str, Any] = {
        "id": case["id"],
        "category": case["category"],
        "customer_id": case["customer_id"],
        "question": case["question"],
        "expected_intent": case["expected_intent"],
        "expected_parameters": case[
            "expected_parameters"
        ],
        "predicted_intent": None,
        "predicted_parameters": {},
        "intent_correct": False,
        "parameter_correct": False,
        "status_correct": False,
        "end_to_end_success": False,
        "expected_status": None,
        "actual_status": None,
        "latency_ms": None,
        "error": None,
        "response": None,
    }

    db = create_connection()

    try:
        provider = provider_factory(case)

        llm_result = provider.extract_intent(
            case["question"]
        )

        predicted_intent = (
            llm_result.intent.value
        )

        predicted_parameters = (
            _normalize_parameters(
                llm_result.parameters
            )
        )

        result["predicted_intent"] = (
            predicted_intent
        )
        result["predicted_parameters"] = (
            predicted_parameters
        )

        result["intent_correct"] = (
            predicted_intent
            == case["expected_intent"]
        )

        result["parameter_correct"] = (
            _parameters_match(
                case["expected_parameters"],
                predicted_parameters,
            )
        )

        service = ChatService(
            llm_client=ReplayEvaluationProvider(
                llm_result
            ),
            intent_router=IntentRouter(),
            response_service=ResponseService(),
        )

        response = service.process_message(
            db=db,
            customer=CustomerContext(
                customer_id=case["customer_id"]
            ),
            message=case["question"],
        )

        result["response"] = response.message
        result["actual_status"] = response.status

        expected_status = (
            TruthStatus.UNSUPPORTED.value
            if case["expected_intent"]
            == Intent.UNSUPPORTED.value
            else TruthStatus.VERIFIED.value
        )

        result["expected_status"] = (
            expected_status
        )

        result["status_correct"] = (
            response.status
            == expected_status
        )

        result["end_to_end_success"] = all(
            [
                result["intent_correct"],
                result["parameter_correct"],
                result["status_correct"],
            ]
        )

    except Exception as exc:
        result["error"] = (
            f"{type(exc).__name__}: {exc}"
        )

    finally:
        db.close()

        elapsed = (
            time.perf_counter()
            - started
        )

        result["latency_ms"] = (
            elapsed * 1000
        )

    return result


def run_evaluation(
    *,
    mode: str = "live",
    dataset_path: Path = DATASET_PATH,
) -> EvaluationRun:
    """
    Run the complete evaluation dataset.

    Modes:

    live:
        Uses the configured Groq model.

    deterministic:
        Uses expected intents as a fake LLM and evaluates the backend
        pipeline independently of Groq.
    """

    dataset = load_dataset(
        dataset_path
    )

    if mode not in {
        "live",
        "deterministic",
    }:
        raise ValueError(
            "mode must be 'live' or 'deterministic'."
        )

    if mode == "live":
        provider_factory = (
            lambda case: GroqEvaluationProvider()
        )
    else:
        provider_factory = (
            lambda case: FakeEvaluationProvider(
                case
            )
        )

    results = [
        _run_single_case(
            case,
            provider_factory,
        )
        for case in dataset
    ]

    return EvaluationRun(
        results=results
    )


def write_results(
    run: EvaluationRun,
    output_path: Path,
) -> None:
    """Write complete evaluation results as JSON."""

    payload = {
        "metrics": {
            "total_cases": run.metrics.total_cases,
            "completed_cases": run.metrics.completed_cases,
            "intent_accuracy": run.metrics.intent_accuracy,
            "parameter_accuracy": (
                run.metrics.parameter_accuracy
            ),
            "status_accuracy": (
                run.metrics.status_accuracy
            ),
            "end_to_end_accuracy": (
                run.metrics.end_to_end_accuracy
            ),
            "unsupported_accuracy": (
                run.metrics.unsupported_accuracy
            ),
            "average_latency_ms": (
                run.metrics.average_latency_ms
            ),
            "p95_latency_ms": (
                run.metrics.p95_latency_ms
            ),
        },
        "category_breakdown": (
            __import__(
                "tests.evaluation.metrics",
                fromlist=["category_breakdown"],
            ).category_breakdown(
                run.results
            )
        ),
        "intent_confusion_matrix": (
            __import__(
                "tests.evaluation.metrics",
                fromlist=["intent_confusion_matrix"],
            ).intent_confusion_matrix(
                run.results
            )
        ),
        "results": run.results,
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )