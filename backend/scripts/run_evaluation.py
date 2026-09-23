"""Command-line runner for NexaTel Phase 1 evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

from tests.evaluation.metrics import (
    category_breakdown,
    format_summary,
    intent_confusion_matrix,
)
from tests.evaluation.runner import (
    DATASET_PATH,
    run_evaluation,
    write_results,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_PATH = (
    BACKEND_ROOT
    / "tests"
    / "evaluation"
    / "results.json"
)


def build_parser() -> argparse.ArgumentParser:
    """Build the evaluation CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the NexaTel Phase 1 evaluation suite."
        )
    )

    parser.add_argument(
        "--mode",
        choices=[
            "live",
            "deterministic",
        ],
        default="live",
        help=(
            "live uses Groq; deterministic bypasses Groq "
            "and evaluates the backend pipeline."
        ),
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATASET_PATH,
        help="Path to the evaluation dataset JSON file.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path where detailed results JSON is written.",
    )

    return parser


def main() -> int:
    """Run the evaluation and print a human-readable summary."""

    parser = build_parser()
    args = parser.parse_args()

    run = run_evaluation(
        mode=args.mode,
        dataset_path=args.dataset,
    )

    print(
        format_summary(
            run.metrics
        )
    )

    print("\nCategory breakdown")
    print("------------------")

    for category, values in category_breakdown(
        run.results
    ).items():
        print(
            f"{category:15} "
            f"{values['total']:>3} cases | "
            f"intent "
            f"{values['intent_accuracy_percent']:>6.2f}% | "
            f"parameters "
            f"{values['parameter_accuracy_percent']:>6.2f}% | "
            f"E2E "
            f"{values['end_to_end_accuracy_percent']:>6.2f}%"
        )

    print("\nIntent confusion matrix")
    print("-----------------------")

    confusion = intent_confusion_matrix(
        run.results
    )

    for expected, predicted_counts in confusion.items():
        print(f"\nExpected: {expected}")

        for predicted, count in sorted(
            predicted_counts.items()
        ):
            print(
                f"  -> {predicted}: {count}"
            )

    write_results(
        run,
        args.output,
    )

    print(
        f"\nDetailed results written to: "
        f"{args.output}"
    )

    failures = [
        result
        for result in run.results
        if not result.get(
            "end_to_end_success",
            False,
        )
    ]

    if failures:
        print(
            f"\nFailed cases: {len(failures)}"
        )

        for result in failures:
            print(
                f"- {result['id']}: "
                f"{result['question']}"
            )

            if result.get("error"):
                print(
                    f"  Error: {result['error']}"
                )
            else:
                print(
                    "  Expected: "
                    f"{result['expected_intent']}"
                )
                print(
                    "  Predicted: "
                    f"{result['predicted_intent']}"
                )
                print(
                    "  Expected parameters: "
                    f"{result['expected_parameters']}"
                )
                print(
                    "  Predicted parameters: "
                    f"{result['predicted_parameters']}"
                )
                print(
                    "  Expected status: "
                    f"{result['expected_status']}"
                )
                print(
                    "  Actual status: "
                    f"{result['actual_status']}"
                )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )