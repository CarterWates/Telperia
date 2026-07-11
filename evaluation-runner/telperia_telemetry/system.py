from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import sleep


@dataclass(frozen=True)
class CpuSnapshot:
    idle: int
    total: int


def read_cpu_snapshot(proc_stat: Path = Path("/proc/stat")) -> CpuSnapshot:
    first_line = proc_stat.read_text().splitlines()[0]
    fields = [int(value) for value in first_line.split()[1:]]
    idle = fields[3] + fields[4]
    return CpuSnapshot(idle=idle, total=sum(fields))


def read_cpu_utilization_percent(delay_s: float = 0.1) -> float:
    start = read_cpu_snapshot()
    sleep(delay_s)
    end = read_cpu_snapshot()

    idle_delta = end.idle - start.idle
    total_delta = end.total - start.total
    if total_delta <= 0:
        return 0.0

    return max(0.0, min(100.0, 100.0 * (1.0 - idle_delta / total_delta)))


def read_memory_used_mb(meminfo: Path = Path("/proc/meminfo")) -> float:
    values: dict[str, int] = {}
    for line in meminfo.read_text().splitlines():
        key, raw_value = line.split(":", 1)
        values[key] = int(raw_value.strip().split()[0])

    total_kb = values["MemTotal"]
    available_kb = values.get("MemAvailable", values.get("MemFree", 0))
    return (total_kb - available_kb) / 1024.0
