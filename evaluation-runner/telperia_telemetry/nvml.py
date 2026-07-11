from __future__ import annotations

import ctypes
from collections.abc import Callable

from telperia_telemetry.errors import TelemetryUnavailableError
from telperia_telemetry.models import GpuMetrics


NVML_SUCCESS = 0


class NvmlMemory(ctypes.Structure):
    _fields_ = [
        ("total", ctypes.c_ulonglong),
        ("free", ctypes.c_ulonglong),
        ("used", ctypes.c_ulonglong),
    ]


class NvmlUtilization(ctypes.Structure):
    _fields_ = [
        ("gpu", ctypes.c_uint),
        ("memory", ctypes.c_uint),
    ]


LibraryLoader = Callable[[], ctypes.CDLL | None]


class NvmlSampler:
    def __init__(self, library_loader: LibraryLoader | None = None, gpu_index: int = 0) -> None:
        self._library_loader = library_loader or _load_nvml_library
        self._gpu_index = gpu_index
        self._lib: ctypes.CDLL | None = None
        self._handle: ctypes.c_void_p | None = None

    def initialize(self) -> None:
        lib = self._library_loader()
        if lib is None:
            raise TelemetryUnavailableError("NVML library is unavailable")

        self._check(lib.nvmlInit_v2())

        handle = ctypes.c_void_p()
        result = lib.nvmlDeviceGetHandleByIndex_v2(ctypes.c_uint(self._gpu_index), ctypes.byref(handle))
        if result != NVML_SUCCESS:
            raise TelemetryUnavailableError("No NVIDIA GPU is available through NVML")

        self._lib = lib
        self._handle = handle

    def shutdown(self) -> None:
        if self._lib is not None:
            self._lib.nvmlShutdown()

    def read_gpu_metrics(self) -> GpuMetrics:
        if self._lib is None or self._handle is None:
            raise TelemetryUnavailableError("NVML sampler has not been initialized")

        lib = self._lib
        handle = self._handle

        utilization = NvmlUtilization()
        self._check(lib.nvmlDeviceGetUtilizationRates(handle, ctypes.byref(utilization)))

        memory = NvmlMemory()
        self._check(lib.nvmlDeviceGetMemoryInfo(handle, ctypes.byref(memory)))

        power_mw = ctypes.c_uint()
        self._check(lib.nvmlDeviceGetPowerUsage(handle, ctypes.byref(power_mw)))

        temperature_c = ctypes.c_uint()
        self._check(lib.nvmlDeviceGetTemperature(handle, ctypes.c_uint(0), ctypes.byref(temperature_c)))

        name_buffer = ctypes.create_string_buffer(96)
        name = None
        if lib.nvmlDeviceGetName(handle, name_buffer, ctypes.c_uint(len(name_buffer))) == NVML_SUCCESS:
            name = name_buffer.value.decode(errors="replace")

        return GpuMetrics(
            index=self._gpu_index,
            name=name,
            utilization_percent=float(utilization.gpu),
            vram_used_mb=memory.used / 1024.0 / 1024.0,
            vram_total_mb=memory.total / 1024.0 / 1024.0,
            power_draw_w=power_mw.value / 1000.0,
            temperature_c=float(temperature_c.value),
        )

    def _check(self, result: int) -> None:
        if result != NVML_SUCCESS:
            raise TelemetryUnavailableError(f"NVML call failed with code {result}")


def _load_nvml_library() -> ctypes.CDLL | None:
    for library_name in ("libnvidia-ml.so.1", "libnvidia-ml.so"):
        try:
            return ctypes.CDLL(library_name)
        except OSError:
            continue
    return None
