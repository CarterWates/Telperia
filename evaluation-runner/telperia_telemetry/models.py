from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class GpuMetrics:
    index: int
    name: str | None
    utilization_percent: float
    vram_used_mb: float
    vram_total_mb: float
    power_draw_w: float
    temperature_c: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TelemetrySample:
    timestamp: datetime
    node_id: str
    gpu: GpuMetrics
    cpu_utilization_percent: float
    system_memory_used_mb: float
    current_model: str | None
    inference_engine: str | None
    request_count: int
    error_count: int

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


@dataclass(frozen=True)
class TelemetryRun:
    node_id: str
    samples: list[TelemetrySample]
    gpu_energy_wh: float
    average_power_w: float
    peak_power_w: float
    sampling_interval_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "gpu_energy_wh": self.gpu_energy_wh,
            "average_power_w": self.average_power_w,
            "peak_power_w": self.peak_power_w,
            "sampling_interval_ms": self.sampling_interval_ms,
            "sample_count": len(self.samples),
            "samples": [sample.to_dict() for sample in self.samples],
        }
