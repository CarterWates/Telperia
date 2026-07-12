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
) -> dict:
    engine_version = client.version()
    results: list[EvaluationResult] = []

    for task in suite.tasks:
        generation = client.generate(model=model_name, prompt=task.prompt)
        score = score_text(generation.text, task.expected_contains) if generation.success else 0.0
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


def score_text(text: str, expected_contains: list[str]) -> float:
    if not expected_contains:
        return 1.0
    normalized = text.lower()
    matches = sum(1 for expected in expected_contains if expected.lower() in normalized)
    return matches / len(expected_contains)
