from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class EvaluationTask:
    task_id: str
    category: str
    prompt: str
    expected_contains: list[str]
    expected_not_contains: list[str] = field(default_factory=list)
    case_sensitive: bool = False
    exact_match: bool = False


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
                expected_not_contains=task.get("expected_not_contains", []),
                case_sensitive=task.get("case_sensitive", False),
                exact_match=task.get("exact_match", False),
            )
            for task in payload["tasks"]
        ],
    )
