from __future__ import annotations

from collections.abc import Iterable


PowerSample = float | tuple[float, float]


def calculate_energy_wh(
    samples: Iterable[PowerSample],
    interval_s: float | None = None,
) -> float:
    """Integrate power readings into watt-hours."""
    if interval_s is not None and interval_s <= 0:
        raise ValueError("interval_s must be greater than zero")

    watt_seconds = 0.0
    for sample in samples:
        if isinstance(sample, tuple):
            power_w, sample_interval_s = sample
        else:
            if interval_s is None:
                raise ValueError("interval_s is required for fixed-interval samples")
            power_w = sample
            sample_interval_s = interval_s

        if power_w < 0:
            raise ValueError("power readings must be non-negative")
        if sample_interval_s <= 0:
            raise ValueError("sample intervals must be greater than zero")

        watt_seconds += power_w * sample_interval_s

    return watt_seconds / 3600.0
