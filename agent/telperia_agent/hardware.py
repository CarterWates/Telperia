from __future__ import annotations

from datetime import UTC, datetime

from telperia_telemetry.system import read_cpu_utilization_percent, read_memory_used_mb

from telperia_agent.telemetry import GpuMetrics, TelemetrySample


def build_hardware_sample(
    *,
    node_id: str,
    gpu: GpuMetrics,
    cpu_utilization_percent: float | None = None,
    system_memory_used_mb: float | None = None,
    current_model: str | None = None,
    inference_engine: str | None = None,
    request_count: int = 0,
    error_count: int = 0,
    timestamp: datetime | None = None,
) -> TelemetrySample:
    if not node_id:
        raise ValueError("node_id is required")
    if request_count < 0 or error_count < 0:
        raise ValueError("request and error counts must be nonnegative")

    return TelemetrySample(
        timestamp=timestamp or datetime.now(UTC),
        node_id=node_id,
        gpu=_normalize_gpu(gpu),
        cpu_utilization_percent=_percentage(cpu_utilization_percent, _read_cpu_percent()),
        system_memory_used_mb=_nonnegative(system_memory_used_mb, _read_memory_used_mb()),
        current_model=current_model,
        inference_engine=inference_engine,
        request_count=int(request_count),
        error_count=int(error_count),
    )


def build_unavailable_hardware_sample(
    *,
    node_id: str,
    current_model: str | None = None,
    inference_engine: str | None = None,
    cpu_utilization_percent: float | None = None,
    system_memory_used_mb: float | None = None,
    request_count: int = 0,
    error_count: int = 0,
    timestamp: datetime | None = None,
) -> TelemetrySample:
    gpu = GpuMetrics(
        index=0,
        name="unavailable",
        utilization_percent=0.0,
        vram_used_mb=0.0,
        vram_total_mb=0.0,
        power_draw_w=0.0,
        temperature_c=0.0,
    )
    return build_hardware_sample(
        node_id=node_id,
        gpu=gpu,
        cpu_utilization_percent=cpu_utilization_percent,
        system_memory_used_mb=system_memory_used_mb,
        current_model=current_model,
        inference_engine=inference_engine,
        request_count=request_count,
        error_count=error_count,
        timestamp=timestamp,
    )


def hardware_sample_record(sample: TelemetrySample) -> dict[str, object]:
    return {"record_type": "hardware_sample", "data": sample.to_dict()}


def _normalize_gpu(gpu: GpuMetrics) -> GpuMetrics:
    return GpuMetrics(
        index=max(0, int(gpu.index)),
        name=(gpu.name or "unavailable").strip() or "unavailable",
        utilization_percent=_percentage(gpu.utilization_percent, 0.0),
        vram_used_mb=_nonnegative(gpu.vram_used_mb, 0.0),
        vram_total_mb=_nonnegative(gpu.vram_total_mb, 0.0),
        power_draw_w=_nonnegative(gpu.power_draw_w, 0.0),
        temperature_c=max(-40.0, min(130.0, float(gpu.temperature_c))),
    )


def _percentage(value: float | None, default: float) -> float:
    raw_value = default if value is None else value
    return max(0.0, min(100.0, float(raw_value)))


def _nonnegative(value: float | None, default: float) -> float:
    raw_value = default if value is None else value
    return max(0.0, float(raw_value))


def _read_cpu_percent() -> float:
    return read_cpu_utilization_percent(delay_s=0)


def _read_memory_used_mb() -> float:
    return read_memory_used_mb()
