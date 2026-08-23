from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from telperia_runner.schema import SchemaValidationError, validate_result_package


FLOAT_TOLERANCE = 1e-6
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

    private_key_path = _find_private_content_key(package)
    if private_key_path is not None:
        return _reject("privacy_violation", f"Result package contains a private content key at {private_key_path}.")

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
    completed_tasks = evaluation["completed_tasks"]
    total_tasks = evaluation["total_tasks"]

    if completed_tasks > total_tasks:
        return _reject("metric_consistency_error", "Completed task count cannot exceed total task count.")

    expected_ratio = completed_tasks / total_tasks if total_tasks else 0.0
    if not _close(evaluation.get("completion_ratio", 0.0), expected_ratio):
        return _reject("metric_consistency_error", "Completion ratio does not match completed and total task counts.")

    tci = scores["tci_v0_1"]
    if not _between(tci["final_score"], 0.0, 100.0):
        return _reject("metric_consistency_error", "TCI final score must be between 0 and 100.")

    for category in tci["categories"].values():
        if not _between(category["category_weight"], 0.0, 1.0):
            return _reject("metric_consistency_error", "TCI category weight must be between 0 and 1.")
        if not _between(category["category_score"], 0.0, 100.0):
            return _reject("metric_consistency_error", "TCI category score must be between 0 and 100.")
        for benchmark in category["benchmarks"]:
            if not _between(benchmark["raw_benchmark_score"], 0.0, 1.0):
                return _reject("metric_consistency_error", "Raw benchmark score must be between 0 and 1.")
            if not _between(benchmark["normalized_benchmark_score"], 0.0, 100.0):
                return _reject("metric_consistency_error", "Normalized benchmark score must be between 0 and 100.")
            if not _close(benchmark["normalized_benchmark_score"], benchmark["raw_benchmark_score"] * 100.0):
                return _reject("metric_consistency_error", "Normalized benchmark score does not match raw score.")

    factual_error = _validate_factual_metrics(scores["factual_reliability_v0_1"])
    if factual_error is not None:
        return factual_error

    if package["performance"]["error_count"] < 0:
        return _reject("metric_consistency_error", "Error count cannot be negative.")

    return None


def _validate_factual_metrics(factual: dict[str, Any]) -> IngestionValidation | None:
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


def _find_private_content_key(value: Any, path: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            current_path = f"{path}.{key}"
            if key.lower() in PRIVATE_CONTENT_KEYS:
                return current_path
            nested = _find_private_content_key(item, current_path)
            if nested is not None:
                return nested
    elif isinstance(value, list):
        for index, item in enumerate(value):
            nested = _find_private_content_key(item, f"{path}[{index}]")
            if nested is not None:
                return nested
    return None


def _between(value: float, minimum: float, maximum: float) -> bool:
    return minimum <= value <= maximum


def _close(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) <= FLOAT_TOLERANCE
