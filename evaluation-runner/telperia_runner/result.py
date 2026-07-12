from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from telperia_runner import RUNNER_VERSION
from telperia_runner.metrics import calculate_completion_ratio, calculate_factual_reliability
from telperia_runner.suite import EvaluationTask


@dataclass(frozen=True)
class EvaluationResult:
    task: EvaluationTask
    success: bool
    score: float
    latency_ms: float
    input_tokens: int
    output_tokens: int
    error_category: str | None


def build_result_package(
    model_name: str,
    model_revision: str,
    quantization: str,
    engine_version: str,
    hardware: dict[str, Any],
    energy: dict[str, Any],
    suite_id: str,
    results: list[EvaluationResult],
    runner_version: str = RUNNER_VERSION,
) -> dict[str, Any]:
    completed_tasks = sum(1 for result in results if result.success)
    total_tasks = len(results)
    completion_ratio = calculate_completion_ratio(completed_tasks, total_tasks)
    factual = _factual_metrics(results)

    return {
        "schema_version": "0.1",
        "run_id": str(uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "model": {
            "name": model_name,
            "revision": model_revision,
            "quantization": quantization,
        },
        "runtime": {
            "engine": "ollama",
            "engine_version": engine_version,
        },
        "hardware": hardware,
        "methodology": {
            "version": "0.1",
            "documents": [
                "docs/telperia-methodology-v0.1.md",
                "methodology/TCI-v0.1.md",
                "methodology/IPW-v0.1.md",
                "methodology/factual-reliability-v0.1.md",
            ],
        },
        "evaluation": {
            "suite": suite_id,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "completion_ratio": completion_ratio,
            "scores": {
                "task_score_average": _average_score(results),
                "tci_v0_1": {
                    "status": "deferred",
                    "reason": "TCI v0.1 weights are not approved in the methodology.",
                },
                "factual_reliability_v0_1": factual,
            },
            "raw_results": [
                {
                    "task_id": result.task.task_id,
                    "category": result.task.category,
                    "score": result.score,
                    "success": result.success,
                    "latency_ms": result.latency_ms,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "error_category": result.error_category,
                }
                for result in results
            ],
        },
        "energy": energy,
        "performance": {
            "input_tokens": sum(result.input_tokens for result in results),
            "output_tokens": sum(result.output_tokens for result in results),
            "tokens_per_second": _tokens_per_second(results),
            "error_count": sum(1 for result in results if not result.success),
        },
        "verification": {
            "level": 0,
            "runner_version": runner_version,
        },
    }


def _average_score(results: list[EvaluationResult]) -> float:
    if not results:
        return 0.0
    return sum(result.score for result in results) / len(results)


def _tokens_per_second(results: list[EvaluationResult]) -> float:
    total_output_tokens = sum(result.output_tokens for result in results)
    total_latency_s = sum(result.latency_ms for result in results) / 1000.0
    if total_latency_s <= 0:
        return 0.0
    return total_output_tokens / total_latency_s


def _factual_metrics(results: list[EvaluationResult]) -> dict[str, float | int]:
    factual_results = [result for result in results if result.task.category == "factual_knowledge"]
    correct = sum(1 for result in factual_results if result.success and result.score >= 1.0)
    incorrect = sum(1 for result in factual_results if result.success and result.score < 1.0)
    abstentions = sum(1 for result in factual_results if not result.success)
    return calculate_factual_reliability(correct, incorrect, abstentions)
