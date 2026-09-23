"""Metrics for the NexaTel Phase 1 evaluation suite."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvaluationMetrics:
    """Aggregate evaluation metrics."""

    total_cases: int
    completed_cases: int
    intent_correct: int
    parameter_correct: int
    status_correct: int
    end_to_end_success: int
    unsupported_correct: int
    average_latency_ms: float
    p95_latency_ms: float

    @property
    def intent_accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return self.intent_correct / self.total_cases

    @property
    def parameter_accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return self.parameter_correct / self.total_cases

    @property
    def status_accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return self.status_correct / self.total_cases

    @property
    def end_to_end_accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return self.end_to_end_success / self.total_cases

    @property
    def unsupported_accuracy(self) -> float:
        unsupported_cases = self.unsupported_correct + 0

        if unsupported_cases == 0:
            return 0.0

        return self.unsupported_correct / unsupported_cases


def _percent(correct: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round(
        (correct / total) * 100,
        2,
    )


def percentile(
    values: list[float],
    percentile_value: float,
) -> float:
    """Calculate a percentile using linear interpolation."""

    if not values:
        return 0.0

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (
        (len(ordered) - 1)
        * percentile_value
        / 100
    )

    lower_index = int(position)
    upper_index = min(
        lower_index + 1,
        len(ordered) - 1,
    )

    weight = position - lower_index

    return (
        ordered[lower_index]
        + (
            ordered[upper_index]
            - ordered[lower_index]
        )
        * weight
    )


def build_metrics(
    results: list[dict[str, Any]],
) -> EvaluationMetrics:
    """Build aggregate metrics from per-case evaluation results."""

    total_cases = len(results)

    completed_cases = sum(
        1
        for result in results
        if not result.get("error")
    )

    intent_correct = sum(
        1
        for result in results
        if result.get("intent_correct") is True
    )

    parameter_correct = sum(
        1
        for result in results
        if result.get("parameter_correct") is True
    )

    status_correct = sum(
        1
        for result in results
        if result.get("status_correct") is True
    )

    end_to_end_success = sum(
        1
        for result in results
        if result.get("end_to_end_success") is True
    )

    unsupported_correct = sum(
        1
        for result in results
        if (
            result.get("expected_intent")
            == "UNSUPPORTED"
            and result.get("intent_correct") is True
        )
    )

    latency_values = [
        float(result["latency_ms"])
        for result in results
        if result.get("latency_ms") is not None
    ]

    return EvaluationMetrics(
        total_cases=total_cases,
        completed_cases=completed_cases,
        intent_correct=intent_correct,
        parameter_correct=parameter_correct,
        status_correct=status_correct,
        end_to_end_success=end_to_end_success,
        unsupported_correct=unsupported_correct,
        average_latency_ms=(
            sum(latency_values) / len(latency_values)
            if latency_values
            else 0.0
        ),
        p95_latency_ms=percentile(
            latency_values,
            95,
        ),
    )


def category_breakdown(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Calculate intent accuracy by evaluation category."""

    grouped: dict[str, list[dict[str, Any]]] = {}

    for result in results:
        category = result.get(
            "category",
            "unknown",
        )

        grouped.setdefault(
            category,
            [],
        ).append(result)

    breakdown: dict[str, dict[str, Any]] = {}

    for category, category_results in sorted(
        grouped.items()
    ):
        total = len(category_results)
        intent_correct = sum(
            1
            for result in category_results
            if result.get("intent_correct") is True
        )

        parameter_correct = sum(
            1
            for result in category_results
            if result.get("parameter_correct") is True
        )

        end_to_end_success = sum(
            1
            for result in category_results
            if result.get("end_to_end_success") is True
        )

        breakdown[category] = {
            "total": total,
            "intent_correct": intent_correct,
            "intent_accuracy_percent": _percent(
                intent_correct,
                total,
            ),
            "parameter_correct": parameter_correct,
            "parameter_accuracy_percent": _percent(
                parameter_correct,
                total,
            ),
            "end_to_end_success": end_to_end_success,
            "end_to_end_accuracy_percent": _percent(
                end_to_end_success,
                total,
            ),
        }

    return breakdown


def intent_confusion_matrix(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Return expected-intent versus predicted-intent counts."""

    matrix: dict[str, Counter[str]] = {}

    for result in results:
        expected = str(
            result.get(
                "expected_intent",
                "UNKNOWN",
            )
        )

        predicted = str(
            result.get(
                "predicted_intent",
                "ERROR",
            )
        )

        matrix.setdefault(
            expected,
            Counter(),
        )[predicted] += 1

    return {
        expected: dict(counter)
        for expected, counter in sorted(
            matrix.items()
        )
    }


def format_summary(
    metrics: EvaluationMetrics,
) -> str:
    """Format aggregate metrics for CLI output."""

    return "\n".join(
        [
            "",
            "NexaTel Phase 1 Evaluation",
            "============================",
            f"Total cases:             {metrics.total_cases}",
            f"Completed cases:         {metrics.completed_cases}",
            (
                "Intent accuracy:        "
                f"{metrics.intent_accuracy * 100:.2f}%"
            ),
            (
                "Parameter accuracy:     "
                f"{metrics.parameter_accuracy * 100:.2f}%"
            ),
            (
                "Status accuracy:        "
                f"{metrics.status_accuracy * 100:.2f}%"
            ),
            (
                "End-to-end accuracy:    "
                f"{metrics.end_to_end_accuracy * 100:.2f}%"
            ),
            (
                "Unsupported accuracy:   "
                f"{metrics.unsupported_accuracy * 100:.2f}%"
            ),
            (
                "Average latency:        "
                f"{metrics.average_latency_ms:.2f} ms"
            ),
            (
                "P95 latency:            "
                f"{metrics.p95_latency_ms:.2f} ms"
            ),
        ]
    )