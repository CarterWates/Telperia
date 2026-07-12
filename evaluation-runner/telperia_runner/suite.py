from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvaluationTask:
    task_id: str
    category: str
    prompt: str
    expected_contains: list[str]


@dataclass(frozen=True)
class EvaluationSuite:
    suite_id: str
    tasks: list[EvaluationTask]


def load_suite(path: Path) -> EvaluationSuite:
    payload = json.loads(path.read_text())
    return EvaluationSuite(
        suite_id=payload["suite_id"],
        tasks=[
            EvaluationTask(
                task_id=task["task_id"],
                category=task["category"],
                prompt=task["prompt"],
                expected_contains=task.get("expected_contains", []),
            )
            for task in payload["tasks"]
        ],
    )
