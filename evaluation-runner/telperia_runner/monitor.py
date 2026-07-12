from __future__ import annotations

from datetime import UTC, datetime
from threading import Event, Thread
from time import sleep
from typing import Any

from telperia_telemetry.energy import calculate_energy_wh
from telperia_telemetry.models import TelemetrySample
from telperia_telemetry.nvml import NvmlSampler
from telperia_telemetry.system import read_cpu_utilization_percent, read_memory_used_mb


def disabled_hardware() -> dict[str, Any]:
    return {
        "gpu": "unavailable",
        "gpu_count": 1,
        "driver": "unavailable",
        "cuda": "unavailable",
        "system_ram_gb": 1,
    }


def disabled_energy() -> dict[str, Any]:
    return {
        "gpu_energy_wh": 0,
        "sampling_interval_ms": 1000,
        "average_power_w": 0,
        "peak_power_w": 0,
        "raw_power_samples": [],
    }


class DisabledMonitor:
    def __enter__(self) -> "DisabledMonitor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def hardware(self) -> dict[str, Any]:
        return disabled_hardware()

    def energy(self) -> dict[str, Any]:
        return disabled_energy()


class NvmlBackgroundMonitor:
    def __init__(self, interval_s: float = 1.0, node_id: str = "local") -> None:
        if interval_s <= 0:
            raise ValueError("interval_s must be greater than zero")
        self.interval_s = interval_s
        self.node_id = node_id
        self._sampler = NvmlSampler()
        self._stop = Event()
        self._thread: Thread | None = None
        self._samples: list[TelemetrySample] = []
        self._ended_at: datetime | None = None

    def __enter__(self) -> "NvmlBackgroundMonitor":
        self._sampler.initialize()
        self._collect_one()
        self._thread = Thread(target=self._collect, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self._ended_at = datetime.now(UTC)
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
        self._sampler.shutdown()

    def hardware(self) -> dict[str, Any]:
        if not self._samples:
            return disabled_hardware()
        gpu = self._samples[0].gpu
        return {
            "gpu": gpu.name or "NVIDIA GPU",
            "gpu_count": 1,
            "driver": "unknown",
            "cuda": "unknown",
            "system_ram_gb": max(1.0, self._samples[0].system_memory_used_mb / 1024.0),
        }

    def energy(self) -> dict[str, Any]:
        if not self._samples:
            return disabled_energy()

        raw_power_samples = self._raw_power_samples()
        power_intervals = [(sample["power_w"], sample["interval_s"]) for sample in raw_power_samples]
        return {
            "gpu_energy_wh": calculate_energy_wh(power_intervals),
            "sampling_interval_ms": int(self.interval_s * 1000),
            "average_power_w": sum(sample.gpu.power_draw_w for sample in self._samples) / len(self._samples),
            "peak_power_w": max(sample.gpu.power_draw_w for sample in self._samples),
            "raw_power_samples": raw_power_samples,
        }

    def _collect(self) -> None:
        while not self._stop.is_set():
            sleep(self.interval_s)
            if not self._stop.is_set():
                self._collect_one()

    def _collect_one(self) -> None:
        self._samples.append(
            TelemetrySample(
                timestamp=datetime.now(UTC),
                node_id=self.node_id,
                gpu=self._sampler.read_gpu_metrics(),
                cpu_utilization_percent=read_cpu_utilization_percent(),
                system_memory_used_mb=read_memory_used_mb(),
                current_model=None,
                inference_engine="ollama",
                request_count=0,
                error_count=0,
            )
        )

    def _raw_power_samples(self) -> list[dict[str, Any]]:
        ended_at = self._ended_at or datetime.now(UTC)
        raw_samples: list[dict[str, Any]] = []
        for index, sample in enumerate(self._samples):
            if index + 1 < len(self._samples):
                interval_s = (self._samples[index + 1].timestamp - sample.timestamp).total_seconds()
            else:
                interval_s = (ended_at - sample.timestamp).total_seconds()
            raw_samples.append(
                {
                    "timestamp": sample.timestamp.isoformat(),
                    "power_w": sample.gpu.power_draw_w,
                    "interval_s": max(interval_s, 0.001),
                }
            )
        return raw_samples


def create_monitor(name: str):
    if name == "disabled":
        return DisabledMonitor()
    if name == "nvml":
        return NvmlBackgroundMonitor()
    raise ValueError("hardware monitor must be disabled or nvml")
