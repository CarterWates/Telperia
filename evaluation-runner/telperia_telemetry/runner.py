from __future__ import annotations

from datetime import UTC, datetime
from math import ceil
from time import sleep

from telperia_telemetry.energy import calculate_energy_wh
from telperia_telemetry.models import TelemetryRun, TelemetrySample
from telperia_telemetry.nvml import NvmlSampler
from telperia_telemetry.system import read_cpu_utilization_percent, read_memory_used_mb


def collect_telemetry(
    duration_s: int,
    interval_s: float = 1.0,
    node_id: str = "local",
    current_model: str | None = None,
    inference_engine: str | None = None,
    sampler: NvmlSampler | None = None,
) -> TelemetryRun:
    if duration_s <= 0:
        raise ValueError("duration_s must be greater than zero")
    if interval_s <= 0:
        raise ValueError("interval_s must be greater than zero")

    nvml_sampler = sampler or NvmlSampler()
    nvml_sampler.initialize()

    samples: list[TelemetrySample] = []
    sample_intervals: list[float] = []
    try:
        sample_count = max(1, ceil(duration_s / interval_s))
        for index in range(sample_count):
            elapsed_s = index * interval_s
            effective_interval_s = min(interval_s, duration_s - elapsed_s)
            samples.append(
                TelemetrySample(
                    timestamp=datetime.now(UTC),
                    node_id=node_id,
                    gpu=nvml_sampler.read_gpu_metrics(),
                    cpu_utilization_percent=read_cpu_utilization_percent(),
                    system_memory_used_mb=read_memory_used_mb(),
                    current_model=current_model,
                    inference_engine=inference_engine,
                    request_count=0,
                    error_count=0,
                )
            )
            sample_intervals.append(effective_interval_s)
            if index < sample_count - 1:
                sleep(effective_interval_s)
    finally:
        nvml_sampler.shutdown()

    power_readings = [sample.gpu.power_draw_w for sample in samples]
    energy_wh = calculate_energy_wh(list(zip(power_readings, sample_intervals)))
    average_power_w = sum(power_readings) / len(power_readings)
    peak_power_w = max(power_readings)

    return TelemetryRun(
        node_id=node_id,
        samples=samples,
        gpu_energy_wh=energy_wh,
        average_power_w=average_power_w,
        peak_power_w=peak_power_w,
        sampling_interval_ms=int(interval_s * 1000),
    )
