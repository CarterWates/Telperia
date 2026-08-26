from __future__ import annotations

import platform
from typing import Any


def build_environment_metadata(
    *,
    operating_system: str | None = None,
    gpu_model: str | None = None,
    driver_version: str | None = None,
    cuda_version: str | None = None,
    inference_engine: str | None = None,
    runtime_version: str | None = None,
    quantization: str | None = None,
) -> dict[str, Any]:
    return {
        "record_type": "environment",
        "operating_system": _known_or_default(operating_system, platform.system() or "unknown"),
        "gpu_model": _known_or_default(gpu_model, "unavailable"),
        "driver_version": _known_or_default(driver_version, "unknown"),
        "cuda_version": _known_or_default(cuda_version, "unavailable"),
        "inference_engine": _known_or_default(inference_engine, "unknown"),
        "runtime_version": _known_or_default(runtime_version, "unknown"),
        "quantization": _known_or_default(quantization, "unknown"),
    }


def _known_or_default(value: str | None, default: str) -> str:
    if value is None:
        return default
    cleaned = value.strip()
    return cleaned or default
