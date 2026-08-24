from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from telperia_runner.metrics import TCI_CATEGORY_WEIGHTS
from telperia_runner.schema import SchemaValidationError, validate_result_package


FLOAT_TOLERANCE = 1e-6
ENERGY_RELATIVE_TOLERANCE = 0.02
MAX_PRIVACY_SCAN_DEPTH = 100
MAX_PRIVACY_SCAN_NODES = 10_000
ACCEPTED_SCHEMA_VERSION = "0.1"
ACCEPTED_METHODOLOGY_VERSION = "0.1"
ACCEPTED_EVALUATION_SUITE = "tci-v0.1"
ACCEPTED_TCI_VERSION = "TCI v0.1"
PRIVATE_CONTENT_KEYS = {
    "prompt",
    "prompts",
    "prompt_text",
    "response",
    "responses",
    "response_text",
    "content",
    "filename",
    "file_path",
    "environment",
    "env",
    "api_key",
    "token",
    "password",
    "secret",
    "hostname",
    "serial_number",
}
PRIVATE_CONTENT_KEY_ALIASES = {re.sub(r"[^a-z0-9]", "", key.lower()) for key in PRIVATE_CONTENT_KEYS} | {
    "prompttext",
    "responsetext",
    "apikey",
    "filepath",
    "serialnumber",
}
SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(^|[\s'\"])(/Users/|/home/|C:\\)"),
    re.compile(r"(^|[\s'\"])\.env(\.|$|[\s'\"])"),
    re.compile(r"\b(prompt|response)\s*:", re.IGNORECASE),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class IngestionValidation:
    accepted: bool
    error_code: str | None = None
    message: str = ""
    validation_warnings: list[str] = field(default_factory=list)


def validate_ingestion_package(package: dict[str, Any], schema_path: Path) -> IngestionValidation:
    try:
        validate_result_package(package, schema_path)
    except SchemaValidationError as exc:
        return _reject("invalid_schema", f"Result package failed schema validation: {exc}")

    structural_error = _validate_required_ingestion_fields(package)
    if structural_error is not None:
        return structural_error

    privacy_violation_path = _find_privacy_violation(package)
    if privacy_violation_path is not None:
        return _reject("privacy_violation", f"Result package contains private content at {privacy_violation_path}.")

    version_error = _validate_versions(package)
    if version_error is not None:
        return version_error

    metric_error = _validate_metric_consistency(package)
    if metric_error is not None:
        return metric_error

    energy_error = _validate_energy_consistency(package)
    if energy_error is not None:
        return energy_error

    return IngestionValidation(accepted=True, validation_warnings=_warning_codes(package))


def extract_observatory_row(
    package: dict[str, Any],
    *,
    result_id: str | None = None,
    published_at: str | None = None,
) -> dict[str, Any]:
    model = package["model"]
    runtime = package["runtime"]
    hardware = package["hardware"]
    environment = package["run_environment"]
    evaluation = package["evaluation"]
    scores = evaluation["scores"]
    factual = scores["factual_reliability_v0_1"]
    ipw = scores["ipw_v0_1"]
    energy = package["energy"]
    confidence = energy.get("energy_confidence")

    gpu = hardware.get("gpu", "unavailable")
    operating_system = environment["operating_system"]
    monitor_backend = environment["monitor_backend"]
    ipw_calculated = "unscaled" in ipw and "displayed" in ipw

    return {
        "result_id": result_id or package["run_id"],
        "run_id": package["run_id"],
        "model_name": model["name"],
        "model_revision": model["revision"],
        "quantization": model["quantization"],
        "runtime_engine": runtime["engine"],
        "runtime_version": runtime["engine_version"],
        "hardware_label": f"{gpu} / {operating_system} / {monitor_backend.upper()}",
        "gpu": gpu,
        "gpu_count": hardware["gpu_count"],
        "operating_system": operating_system,
        "monitor_backend": monitor_backend,
        "tci_v0_1": scores["tci_v0_1"]["final_score"],
        "factual_correctness_rate": factual["correctness_rate"],
        "factual_incorrect_answer_rate": factual["incorrect_answer_rate"],
        "factual_abstention_rate": factual["abstention_rate"],
        "factual_attempted_accuracy": factual["attempted_accuracy"],
        "local_ipw_unscaled": ipw["unscaled"] if ipw_calculated else None,
        "local_ipw_displayed": ipw["displayed"] if ipw_calculated else None,
        "local_ipw_status": "calculated" if ipw_calculated else ipw["status"],
        "gpu_energy_wh": energy["gpu_energy_wh"],
        "energy_confidence": confidence["quality"] if confidence is not None else None,
        "energy_warning_codes": confidence["warning_codes"] if confidence is not None else [],
        "verification_level": package["verification"]["level"],
        "methodology_version": package["methodology"]["version"],
        "evaluation_suite": evaluation["suite"],
        "completed_tasks": evaluation["completed_tasks"],
        "total_tasks": evaluation["total_tasks"],
        "completion_ratio": evaluation.get("completion_ratio", 0.0),
        "error_count": package["performance"]["error_count"],
        "result_timestamp": package["timestamp"],
        "published_at": published_at or package["timestamp"],
    }


def _reject(error_code: str, message: str) -> IngestionValidation:
    return IngestionValidation(accepted=False, error_code=error_code, message=message)


def _validate_versions(package: dict[str, Any]) -> IngestionValidation | None:
    if package["schema_version"] != ACCEPTED_SCHEMA_VERSION:
        return _reject("unsupported_schema_version", "Result package schema version is not supported.")
    if package["methodology"]["version"] != ACCEPTED_METHODOLOGY_VERSION:
        return _reject("unsupported_methodology_version", "Result package methodology version is not supported.")
    if package["evaluation"]["suite"] != ACCEPTED_EVALUATION_SUITE:
        return _reject("unsupported_evaluation_suite", "Result package evaluation suite is not supported.")
    if package["evaluation"]["scores"]["tci_v0_1"]["methodology_version"] != ACCEPTED_TCI_VERSION:
        return _reject("unsupported_methodology_version", "Result package TCI methodology version is not supported.")
    return None


def _validate_metric_consistency(package: dict[str, Any]) -> IngestionValidation | None:
    evaluation = package["evaluation"]
    scores = evaluation["scores"]
    raw_results = evaluation["raw_results"]
    completed_tasks = evaluation["completed_tasks"]
    total_tasks = evaluation["total_tasks"]

    if completed_tasks > total_tasks:
        return _reject("metric_consistency_error", "Completed task count cannot exceed total task count.")
    if total_tasks != len(raw_results):
        return _reject("metric_consistency_error", "Total task count does not match raw result count.")

    expected_completed = sum(1 for result in raw_results if result.get("success") is True)
    if completed_tasks != expected_completed:
        return _reject("metric_consistency_error", "Completed task count does not match successful raw results.")

    if package["performance"]["error_count"] != sum(1 for result in raw_results if result.get("success") is not True):
        return _reject("metric_consistency_error", "Error count does not match failed raw results.")

    raw_scores = []
    raw_result_scores_by_task: dict[str, float] = {}
    for result in raw_results:
        score = float(result["score"])
        if not _between(score, 0.0, 1.0):
            return _reject("metric_consistency_error", "Raw result score must be between 0 and 1.")
        raw_scores.append(score)
        raw_result_scores_by_task[result["task_id"]] = score

    if not _close(scores["task_score_average"], _average(raw_scores)):
        return _reject("metric_consistency_error", "Task score average does not match raw result scores.")

    expected_ratio = completed_tasks / total_tasks if total_tasks else 0.0
    if not _close(evaluation.get("completion_ratio", 0.0), expected_ratio):
        return _reject("metric_consistency_error", "Completion ratio does not match completed and total task counts.")

    tci = scores["tci_v0_1"]
    if not _between(tci["final_score"], 0.0, 100.0):
        return _reject("metric_consistency_error", "TCI final score must be between 0 and 100.")

    expected_final_score = 0.0
    for category_name, category in tci["categories"].items():
        expected_weight = TCI_CATEGORY_WEIGHTS.get(category_name)
        if expected_weight is None:
            return _reject("metric_consistency_error", "TCI includes an unsupported category.")
        if not _between(category["category_weight"], 0.0, 1.0):
            return _reject("metric_consistency_error", "TCI category weight must be between 0 and 1.")
        if not _close(category["category_weight"], expected_weight):
            return _reject("metric_consistency_error", "TCI category weight does not match the methodology.")
        if not _between(category["category_score"], 0.0, 100.0):
            return _reject("metric_consistency_error", "TCI category score must be between 0 and 100.")
        normalized_scores = []
        for benchmark in category["benchmarks"]:
            if not _between(benchmark["raw_benchmark_score"], 0.0, 1.0):
                return _reject("metric_consistency_error", "Raw benchmark score must be between 0 and 1.")
            if not _between(benchmark["normalized_benchmark_score"], 0.0, 100.0):
                return _reject("metric_consistency_error", "Normalized benchmark score must be between 0 and 100.")
            if not _close(benchmark["normalized_benchmark_score"], benchmark["raw_benchmark_score"] * 100.0):
                return _reject("metric_consistency_error", "Normalized benchmark score does not match raw score.")
            raw_result_score = raw_result_scores_by_task.get(benchmark["task_id"])
            if raw_result_score is not None and not _close(benchmark["raw_benchmark_score"], raw_result_score):
                return _reject("metric_consistency_error", "TCI benchmark score does not match raw result score.")
            normalized_scores.append(benchmark["normalized_benchmark_score"])

        expected_category_score = _average(normalized_scores)
        if not _close(category["category_score"], expected_category_score):
            return _reject("metric_consistency_error", "TCI category score does not match benchmark scores.")
        expected_final_score += expected_weight * expected_category_score

    if not _close(tci["final_score"], expected_final_score):
        return _reject("metric_consistency_error", "TCI final score does not match category scores and weights.")

    factual_error = _validate_factual_metrics(scores["factual_reliability_v0_1"], raw_results)
    if factual_error is not None:
        return factual_error

    return None


def _validate_factual_metrics(factual: dict[str, Any], raw_results: list[dict[str, Any]]) -> IngestionValidation | None:
    correct = factual["correct_responses"]
    incorrect = factual["incorrect_responses"]
    abstentions = factual["abstentions"]
    total = factual["total_questions"]
    attempted = correct + incorrect

    if correct + incorrect + abstentions != total:
        return _reject("metric_consistency_error", "Factual Reliability counts do not add up to total questions.")

    expected_rates = {
        "correctness_rate": correct / total if total else 0.0,
        "incorrect_answer_rate": incorrect / total if total else 0.0,
        "abstention_rate": abstentions / total if total else 0.0,
        "attempted_accuracy": correct / attempted if attempted else 0.0,
    }
    for key, expected in expected_rates.items():
        if not _between(factual[key], 0.0, 1.0):
            return _reject("metric_consistency_error", "Factual Reliability rates must be between 0 and 1.")
        if not _close(factual[key], expected):
            return _reject("metric_consistency_error", f"Factual Reliability {key} does not match counts.")

    factual_results = [result for result in raw_results if result["category"] == "factual_knowledge"]
    expected_correct = sum(1 for result in factual_results if result.get("success") is True and float(result["score"]) >= 1.0)
    expected_incorrect = sum(1 for result in factual_results if result.get("success") is True and float(result["score"]) < 1.0)
    expected_abstentions = sum(1 for result in factual_results if result.get("success") is not True)
    if (correct, incorrect, abstentions) != (expected_correct, expected_incorrect, expected_abstentions):
        return _reject("metric_consistency_error", "Factual Reliability counts do not match factual raw results.")

    return None


def _validate_energy_consistency(package: dict[str, Any]) -> IngestionValidation | None:
    evaluation = package["evaluation"]
    scores = evaluation["scores"]
    tci_score = scores["tci_v0_1"]["final_score"]
    completion_ratio = evaluation.get("completion_ratio", 0.0)
    ipw = scores["ipw_v0_1"]
    energy = package["energy"]
    gpu_energy_wh = energy["gpu_energy_wh"]

    if "unscaled" in ipw:
        if gpu_energy_wh <= 0:
            return _reject("energy_consistency_error", "Calculated Local IPW requires positive GPU energy.")
        if energy.get("energy_scope") != "local_inference_hardware":
            return _reject("energy_consistency_error", "Calculated Local IPW requires local inference hardware scope.")
        if energy.get("energy_source") != "local_gpu_telemetry":
            return _reject("energy_consistency_error", "Calculated Local IPW requires local GPU telemetry.")
        if energy.get("monitor_backend") != "nvml":
            return _reject("energy_consistency_error", "Calculated Local IPW requires the NVML monitor backend.")
        if not energy.get("raw_power_samples"):
            return _reject("energy_consistency_error", "Calculated Local IPW requires raw power samples.")
        sample_error = _validate_power_sample_summary(energy)
        if sample_error is not None:
            return sample_error

        expected_unscaled = tci_score * completion_ratio / gpu_energy_wh
        if not _close(ipw["unscaled"], expected_unscaled):
            return _reject("energy_consistency_error", "Unscaled Local IPW does not match TCI, completion ratio, and energy.")
        if not _close(ipw["displayed"], 1000.0 * ipw["unscaled"]):
            return _reject("energy_consistency_error", "Displayed Local IPW does not match the unscaled value.")
    else:
        if ipw.get("status") != "deferred":
            return _reject("energy_consistency_error", "Unavailable Local IPW must use deferred status.")
        if ipw.get("energy_source") != "unavailable":
            return _reject("energy_consistency_error", "Deferred Local IPW must use unavailable energy source.")
        if gpu_energy_wh != 0:
            return _reject("energy_consistency_error", "Deferred Local IPW should report zero GPU energy.")

    return _validate_energy_confidence(energy)


def _validate_required_ingestion_fields(package: dict[str, Any]) -> IngestionValidation | None:
    if "run_environment" not in package:
        return _reject("invalid_schema", "Result package must include run environment metadata for ingestion.")
    if not package.get("evaluation", {}).get("raw_results"):
        return _reject("invalid_schema", "Result package must include raw evaluation results for ingestion.")

    try:
        UUID(package["run_id"])
    except (TypeError, ValueError):
        return _reject("invalid_schema", "Result package run_id must be a valid UUID.")

    if not _is_parseable_timestamp(package["timestamp"]):
        return _reject("invalid_schema", "Result package timestamp must be a parseable timestamp.")

    for sample in package.get("energy", {}).get("raw_power_samples", []):
        if not _is_parseable_timestamp(sample["timestamp"]):
            return _reject("invalid_schema", "Raw power sample timestamp must be a parseable timestamp.")

    return None


def _validate_power_sample_summary(energy: dict[str, Any]) -> IngestionValidation | None:
    samples = energy.get("raw_power_samples", [])
    intervals = [float(sample["interval_s"]) for sample in samples if "interval_s" in sample]
    if len(intervals) != len(samples):
        return None

    power_values = [float(sample["power_w"]) for sample in samples]
    if any(power_w < 0 for power_w in power_values) or any(interval_s < 0 for interval_s in intervals):
        return _reject("energy_consistency_error", "Raw power samples cannot contain negative values.")

    measured_duration = sum(intervals)
    if measured_duration <= 0:
        return _reject("energy_consistency_error", "Raw power samples must cover a positive measured duration.")

    watt_seconds = sum(power_w * interval_s for power_w, interval_s in zip(power_values, intervals))
    expected_energy_wh = watt_seconds / 3600.0
    expected_average_power_w = watt_seconds / measured_duration
    expected_peak_power_w = max(power_values)

    checks = [
        ("gpu_energy_wh", expected_energy_wh, "GPU energy does not match raw power samples."),
        ("average_power_w", expected_average_power_w, "Average power does not match raw power samples."),
        ("peak_power_w", expected_peak_power_w, "Peak power does not match raw power samples."),
    ]
    for key, expected, message in checks:
        if not _close_energy(float(energy[key]), expected):
            return _reject("energy_consistency_error", message)

    return None


def _validate_energy_confidence(energy: dict[str, Any]) -> IngestionValidation | None:
    confidence = energy.get("energy_confidence")
    if confidence is None:
        return None

    samples = energy.get("raw_power_samples", [])
    if confidence["sample_count"] != len(samples):
        return _reject("energy_consistency_error", "Energy confidence sample count does not match raw samples.")

    intervals = [float(sample["interval_s"]) for sample in samples if "interval_s" in sample]
    if intervals and not _close(confidence["measured_duration_s"], sum(intervals)):
        return _reject("energy_consistency_error", "Energy confidence duration does not match sample intervals.")

    return None


def _warning_codes(package: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    energy = package["energy"]
    confidence = energy.get("energy_confidence")
    ipw = package["evaluation"]["scores"]["ipw_v0_1"]

    if confidence is None:
        warnings.append("energy_confidence_missing")
    elif confidence["quality"] == "low":
        warnings.append("low_energy_confidence")

    if package["verification"]["level"] == 0:
        warnings.append("verification_level_zero")

    if ipw.get("status") == "deferred":
        warnings.append("ipw_deferred")

    return warnings


def _find_privacy_violation(value: Any) -> str | None:
    stack: list[tuple[Any, str, int]] = [(value, "$", 0)]
    visited_nodes = 0

    while stack:
        current, path, depth = stack.pop()
        visited_nodes += 1
        if visited_nodes > MAX_PRIVACY_SCAN_NODES or depth > MAX_PRIVACY_SCAN_DEPTH:
            return path

        if isinstance(current, dict):
            for key, item in current.items():
                current_path = f"{path}.{key}"
                if _normalize_key(str(key)) in PRIVATE_CONTENT_KEY_ALIASES:
                    return current_path
                stack.append((item, current_path, depth + 1))
        elif isinstance(current, list):
            for index, item in enumerate(current):
                stack.append((item, f"{path}[{index}]", depth + 1))
        elif isinstance(current, str) and _looks_sensitive_value(current):
            return path

    return None


def _looks_sensitive_value(value: str) -> bool:
    return any(pattern.search(value) for pattern in SENSITIVE_VALUE_PATTERNS)


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _is_parseable_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    return True


def _between(value: float, minimum: float, maximum: float) -> bool:
    return minimum <= value <= maximum


def _close(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) <= FLOAT_TOLERANCE


def _close_energy(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) <= max(FLOAT_TOLERANCE, abs(float(right)) * ENERGY_RELATIVE_TOLERANCE)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
