from __future__ import annotations


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
