from __future__ import annotations

from collections.abc import Iterable
from typing import Any


TCI_CATEGORY_WEIGHTS = {
    "reasoning": 0.25,
    "coding": 0.25,
    "mathematics": 0.20,
    "factual_knowledge": 0.15,
    "instruction_adherence": 0.15,
}


def calculate_completion_ratio(completed_tasks: int, total_tasks: int) -> float:
    if completed_tasks < 0 or total_tasks < 0:
        raise ValueError("task counts must be non-negative")
    if completed_tasks > total_tasks:
        raise ValueError("completed_tasks cannot exceed total_tasks")
    if total_tasks == 0:
        return 0.0
    return completed_tasks / total_tasks


def calculate_factual_reliability(correct: int, incorrect: int, abstentions: int) -> dict[str, float | int]:
    if min(correct, incorrect, abstentions) < 0:
        raise ValueError("factual reliability counts must be non-negative")

    total = correct + incorrect + abstentions
    attempted = correct + incorrect
    return {
        "correct_responses": correct,
        "incorrect_responses": incorrect,
        "abstentions": abstentions,
        "total_questions": total,
        "correctness_rate": correct / total if total else 0.0,
        "incorrect_answer_rate": incorrect / total if total else 0.0,
        "abstention_rate": abstentions / total if total else 0.0,
        "attempted_accuracy": correct / attempted if attempted else 0.0,
    }


def calculate_tci(results: Iterable[Any]) -> dict[str, Any]:
    by_category: dict[str, list[Any]] = {category: [] for category in TCI_CATEGORY_WEIGHTS}
    for result in results:
        if result.task.category in by_category:
            by_category[result.task.category].append(result)

    categories: dict[str, Any] = {}
    final_score = 0.0
    for category, weight in TCI_CATEGORY_WEIGHTS.items():
        benchmarks = [_benchmark_score(result) for result in by_category[category]]
        category_score = _average([benchmark["normalized_benchmark_score"] for benchmark in benchmarks])
        final_score += weight * category_score
        categories[category] = {
            "category_weight": weight,
            "category_score": category_score,
            "benchmarks": benchmarks,
        }

    return {
        "methodology_version": "TCI v0.1",
        "final_score": final_score,
        "categories": categories,
    }


def calculate_ipw(tci: float, completion_ratio: float, gpu_energy_wh: float) -> dict[str, float]:
    if gpu_energy_wh <= 0:
        raise ValueError("gpu_energy_wh must be greater than zero")
    if tci < 0:
        raise ValueError("tci must be non-negative")
    if not 0 <= completion_ratio <= 1:
        raise ValueError("completion_ratio must be between 0 and 1")

    unscaled = tci * completion_ratio / gpu_energy_wh
    return {
        "unscaled": unscaled,
        "displayed": 1000.0 * unscaled,
    }


def _benchmark_score(result: Any) -> dict[str, float | str]:
    raw_score = float(result.score)
    if not 0.0 <= raw_score <= 1.0:
        raise ValueError("raw benchmark score must be between 0 and 1")
    return {
        "task_id": result.task.task_id,
        "raw_benchmark_score": raw_score,
        "normalized_benchmark_score": raw_score * 100.0,
    }


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
