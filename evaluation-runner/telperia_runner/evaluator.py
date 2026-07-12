from __future__ import annotations

from collections.abc import Callable
from typing import Any

from telperia_runner.ollama import OllamaClient
from telperia_runner.result import EvaluationResult, build_result_package
from telperia_runner.suite import EvaluationSuite


def run_evaluation(
    suite: EvaluationSuite,
    model_name: str,
    client: OllamaClient,
    hardware: dict,
    energy: dict[str, Any] | Callable[[], dict[str, Any]],
    model_revision: str = "unknown",
    quantization: str = "unknown",
    max_output_tokens: int = 64,
) -> dict:
    engine_version = client.version()
    results: list[EvaluationResult] = []

    for task in suite.tasks:
        generation = client.generate(model=model_name, prompt=task.prompt, max_output_tokens=max_output_tokens)
        score = score_text(generation.text, task) if generation.success else 0.0
        results.append(
            EvaluationResult(
                task=task,
                success=generation.success,
                score=score,
                latency_ms=generation.latency_ms,
                input_tokens=generation.input_tokens,
                output_tokens=generation.output_tokens,
                error_category=generation.error_category,
            )
        )

    energy_snapshot = energy() if callable(energy) else energy

    return build_result_package(
        model_name=model_name,
        model_revision=model_revision,
        quantization=quantization,
        engine_version=engine_version,
        hardware=hardware,
        energy=energy_snapshot,
        suite_id=suite.suite_id,
        results=results,
    )


def score_text(text: str, task: EvaluationTask) -> float:
    if not task.expected_contains:
        return 1.0

    candidate = text.strip()
    expected_values = [item.strip() for item in task.expected_contains]
    forbidden_values = [item.strip() for item in task.expected_not_contains]
    if not task.case_sensitive:
        candidate = candidate.lower()
        expected_values = [item.lower() for item in expected_values]
        forbidden_values = [item.lower() for item in forbidden_values]

    if any(forbidden and forbidden in candidate for forbidden in forbidden_values):
        return 0.0

    if task.exact_match:
        return 1.0 if any(candidate == expected for expected in expected_values) else 0.0

    matches = sum(1 for expected in expected_values if expected and expected in candidate)
    return matches / len(expected_values)
