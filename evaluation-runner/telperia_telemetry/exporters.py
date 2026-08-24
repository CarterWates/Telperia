from __future__ import annotations

import csv
import json
from pathlib import Path

from telperia_telemetry.models import TelemetryRun


CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")


def write_json(run: TelemetryRun, output_path: Path) -> None:
    output_path.write_text(json.dumps(run.to_dict(), indent=2) + "\n")


def write_csv(run: TelemetryRun, output_path: Path) -> None:
    fieldnames = [
        "timestamp",
        "node_id",
        "gpu_index",
        "gpu_name",
        "gpu_utilization_percent",
        "gpu_vram_used_mb",
        "gpu_vram_total_mb",
        "gpu_power_draw_w",
        "gpu_temperature_c",
        "cpu_utilization_percent",
        "system_memory_used_mb",
        "current_model",
        "inference_engine",
        "request_count",
        "error_count",
    ]

    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for sample in run.samples:
            row = {
                "timestamp": sample.timestamp.isoformat(),
                "node_id": sample.node_id,
                "gpu_index": sample.gpu.index,
                "gpu_name": sample.gpu.name or "",
                "gpu_utilization_percent": sample.gpu.utilization_percent,
                "gpu_vram_used_mb": sample.gpu.vram_used_mb,
                "gpu_vram_total_mb": sample.gpu.vram_total_mb,
                "gpu_power_draw_w": sample.gpu.power_draw_w,
                "gpu_temperature_c": sample.gpu.temperature_c,
                "cpu_utilization_percent": sample.cpu_utilization_percent,
                "system_memory_used_mb": sample.system_memory_used_mb,
                "current_model": sample.current_model or "",
                "inference_engine": sample.inference_engine or "",
                "request_count": sample.request_count,
                "error_count": sample.error_count,
            }
            writer.writerow(_safe_csv_row(row))


def _safe_csv_row(row: dict[str, object]) -> dict[str, object]:
    return {key: _safe_csv_cell(value) for key, value in row.items()}


def _safe_csv_cell(value: object) -> object:
    if isinstance(value, str) and value.startswith(CSV_FORMULA_PREFIXES):
        return "'" + value
    return value
