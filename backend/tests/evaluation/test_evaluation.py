"""Tests for the NexaTel evaluation framework."""

from pathlib import Path

from tests.evaluation.metrics import (
    build_metrics,
    category_breakdown,
    intent_confusion_matrix,
    percentile,
)
from tests.evaluation.runner import (
    load_dataset,
    run_evaluation,
)


def test_evaluation_dataset_has_expected_size():
    dataset = load_dataset()

    assert 50 <= len(dataset) <= 100


def test_evaluation_dataset_has_unique_ids():
    dataset = load_dataset()

    ids = [
        case["id"]
        for case in dataset
    ]

    assert len(ids) == len(set(ids))


def test_percentile_empty_values():
    assert percentile([], 95) == 0.0


def test_percentile_single_value():
    assert percentile([100.0], 95) == 100.0


def test_percentile_multiple_values():
    value = percentile(
        [10.0, 20.0, 30.0, 40.0],
        95,
    )

    assert value == 38.5


def test_build_metrics():
    results = [
        {
            "intent_correct": True,
            "parameter_correct": True,
            "status_correct": True,
            "end_to_end_success": True,
            "latency_ms": 100.0,
            "expected_intent": "GET_CURRENT_PLAN",
            "category": "plans",
        },
        {
            "intent_correct": False,
            "parameter_correct": True,
            "status_correct": False,
            "end_to_end_success": False,
            "latency_ms": 200.0,
            "expected_intent": "GET_ACCOUNT_STATUS",
            "category": "account",
        },
        {
            "intent_correct": True,
            "parameter_correct": True,
            "status_correct": True,
            "end_to_end_success": True,
            "latency_ms": 300.0,
            "expected_intent": "UNSUPPORTED",
            "category": "unsupported",
        },
    ]

    metrics = build_metrics(results)

    assert metrics.total_cases == 3
    assert metrics.completed_cases == 3
    assert metrics.intent_correct == 2
    assert metrics.parameter_correct == 3
    assert metrics.status_correct == 2
    assert metrics.end_to_end_success == 2
    assert metrics.unsupported_correct == 1
    assert metrics.average_latency_ms == 200.0
    assert metrics.p95_latency_ms == 290.0


def test_category_breakdown():
    results = [
        {
            "category": "plans",
            "intent_correct": True,
            "parameter_correct": True,
            "end_to_end_success": True,
        },
        {
            "category": "plans",
            "intent_correct": False,
            "parameter_correct": True,
            "end_to_end_success": False,
        },
    ]

    breakdown = category_breakdown(
        results
    )

    assert breakdown["plans"]["total"] == 2
    assert (
        breakdown["plans"]["intent_accuracy_percent"]
        == 50.0
    )
    assert (
        breakdown["plans"][
            "parameter_accuracy_percent"
        ]
        == 100.0
    )


def test_intent_confusion_matrix():
    results = [
        {
            "expected_intent": "GET_CURRENT_PLAN",
            "predicted_intent": "GET_CURRENT_PLAN",
        },
        {
            "expected_intent": "GET_CURRENT_PLAN",
            "predicted_intent": "GET_ACCOUNT_STATUS",
        },
        {
            "expected_intent": "UNSUPPORTED",
            "predicted_intent": "UNSUPPORTED",
        },
    ]

    matrix = intent_confusion_matrix(
        results
    )

    assert (
        matrix["GET_CURRENT_PLAN"][
            "GET_CURRENT_PLAN"
        ]
        == 1
    )

    assert (
        matrix["GET_CURRENT_PLAN"][
            "GET_ACCOUNT_STATUS"
        ]
        == 1
    )

    assert (
        matrix["UNSUPPORTED"][
            "UNSUPPORTED"
        ]
        == 1
    )


def test_deterministic_evaluation_runs_end_to_end():
    run = run_evaluation(
        mode="deterministic"
    )

    assert len(run.results) == 68

    assert run.metrics.intent_accuracy == 1.0
    assert run.metrics.parameter_accuracy == 1.0
    assert run.metrics.status_accuracy == 1.0
    assert run.metrics.end_to_end_accuracy == 1.0

    assert all(
        result["error"] is None
        for result in run.results
    )