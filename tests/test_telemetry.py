import csv
import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stderr
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
sys.path.insert(0, str(RUNNER_ROOT))

from telperia_telemetry.energy import calculate_energy_wh
from telperia_telemetry.errors import TelemetryUnavailableError
from telperia_telemetry.exporters import write_csv, write_json
from telperia_telemetry.models import GpuMetrics, TelemetryRun, TelemetrySample
from telperia_telemetry.nvml import NvmlSampler
from telperia_telemetry.runner import collect_telemetry


TELEMETRY_CLI_PATH = RUNNER_ROOT / "telemetry.py"


class EnergyTests(unittest.TestCase):
    def test_integrates_fixed_interval_power_samples(self) -> None:
        samples = [100.0, 110.0, 90.0]

        energy_wh = calculate_energy_wh(samples, interval_s=1.0)

        self.assertAlmostEqual(energy_wh, 300.0 / 3600.0)

    def test_integrates_variable_interval_power_samples(self) -> None:
        samples = [(100.0, 0.5), (120.0, 1.5)]

        energy_wh = calculate_energy_wh(samples)

        self.assertAlmostEqual(energy_wh, 230.0 / 3600.0)

    def test_rejects_negative_power(self) -> None:
        with self.assertRaises(ValueError):
            calculate_energy_wh([-1.0], interval_s=1.0)


class ExportTests(unittest.TestCase):
    def test_writes_json_result_with_samples_and_energy(self) -> None:
        sample = make_sample(power_w=120.0)
        run = TelemetryRun(
            node_id="local",
            samples=[sample],
            gpu_energy_wh=120.0 / 3600.0,
            average_power_w=120.0,
            peak_power_w=120.0,
            sampling_interval_ms=1000,
        )

        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "telemetry.json"
            write_json(run, output)

            payload = json.loads(output.read_text())

        self.assertEqual(payload["node_id"], "local")
        self.assertAlmostEqual(payload["gpu_energy_wh"], 120.0 / 3600.0)
        self.assertEqual(payload["samples"][0]["gpu"]["power_draw_w"], 120.0)

    def test_writes_csv_rows_for_samples(self) -> None:
        run = TelemetryRun(
            node_id="local",
            samples=[make_sample(power_w=75.0)],
            gpu_energy_wh=75.0 / 3600.0,
            average_power_w=75.0,
            peak_power_w=75.0,
            sampling_interval_ms=1000,
        )

        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "telemetry.csv"
            write_csv(run, output)

            rows = list(csv.DictReader(output.read_text().splitlines()))

        self.assertEqual(rows[0]["node_id"], "local")
        self.assertEqual(rows[0]["gpu_power_draw_w"], "75.0")
        self.assertEqual(rows[0]["current_model"], "")


class NvmlSamplerTests(unittest.TestCase):
    def test_raises_clear_error_when_nvml_library_is_missing(self) -> None:
        sampler = NvmlSampler(library_loader=lambda: None)

        with self.assertRaisesRegex(TelemetryUnavailableError, "NVML"):
            sampler.initialize()

    def test_shuts_down_nvml_when_gpu_handle_lookup_fails(self) -> None:
        fake_lib = FakeNvmlLibrary(handle_result=1)
        sampler = NvmlSampler(library_loader=lambda: fake_lib)

        with self.assertRaisesRegex(TelemetryUnavailableError, "No NVIDIA GPU"):
            sampler.initialize()

        self.assertEqual(fake_lib.shutdown_calls, 1)


class RunnerTests(unittest.TestCase):
    def test_short_duration_uses_actual_duration_for_energy(self) -> None:
        sampler = FakeSampler(power_w=100.0)

        with patch("telperia_telemetry.runner.read_cpu_utilization_percent", return_value=0.0):
            with patch("telperia_telemetry.runner.read_memory_used_mb", return_value=0.0):
                run = collect_telemetry(duration_s=1, interval_s=10.0, sampler=sampler)

        self.assertEqual(len(run.samples), 1)
        self.assertAlmostEqual(run.gpu_energy_wh, 100.0 / 3600.0)
        self.assertEqual(sampler.shutdown_calls, 1)


class CliTests(unittest.TestCase):
    def test_cli_rejects_unsupported_output_extension_before_writing(self) -> None:
        module = load_telemetry_cli()
        original_argv = sys.argv
        original_collect = module.collect_telemetry
        try:
            sys.argv = ["telemetry.py", "--duration", "1", "--output", "telemetry.txt"]
            module.collect_telemetry = lambda **_: make_run()

            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    module.main()
        finally:
            sys.argv = original_argv
            module.collect_telemetry = original_collect

        self.assertEqual(raised.exception.code, 2)

    def test_cli_writes_json_output(self) -> None:
        module = load_telemetry_cli()
        original_argv = sys.argv
        original_collect = module.collect_telemetry
        try:
            with TemporaryDirectory() as tmpdir:
                output = Path(tmpdir) / "telemetry.json"
                sys.argv = ["telemetry.py", "--duration", "1", "--output", str(output)]
                module.collect_telemetry = lambda **_: make_run()

                exit_code = module.main()

                payload = json.loads(output.read_text())
        finally:
            sys.argv = original_argv
            module.collect_telemetry = original_collect

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["node_id"], "local")


def load_telemetry_cli():
    spec = importlib.util.spec_from_file_location("telemetry_cli", TELEMETRY_CLI_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load telemetry CLI")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_run() -> TelemetryRun:
    return TelemetryRun(
        node_id="local",
        samples=[make_sample(power_w=80.0)],
        gpu_energy_wh=80.0 / 3600.0,
        average_power_w=80.0,
        peak_power_w=80.0,
        sampling_interval_ms=1000,
    )


class FakeNvmlLibrary:
    def __init__(self, handle_result: int) -> None:
        self.handle_result = handle_result
        self.shutdown_calls = 0

    def nvmlInit_v2(self) -> int:
        return 0

    def nvmlDeviceGetHandleByIndex_v2(self, *_args) -> int:
        return self.handle_result

    def nvmlShutdown(self) -> int:
        self.shutdown_calls += 1
        return 0


class FakeSampler:
    def __init__(self, power_w: float) -> None:
        self.power_w = power_w
        self.shutdown_calls = 0

    def initialize(self) -> None:
        return None

    def shutdown(self) -> None:
        self.shutdown_calls += 1

    def read_gpu_metrics(self) -> GpuMetrics:
        return GpuMetrics(
            index=0,
            name="NVIDIA Test GPU",
            utilization_percent=10.0,
            vram_used_mb=512.0,
            vram_total_mb=8192.0,
            power_draw_w=self.power_w,
            temperature_c=50.0,
        )


def make_sample(power_w: float) -> TelemetrySample:
    return TelemetrySample(
        timestamp=datetime(2026, 7, 11, 12, 0, tzinfo=UTC),
        node_id="local",
        gpu=GpuMetrics(
            index=0,
            name="NVIDIA Test GPU",
            utilization_percent=50.0,
            vram_used_mb=1024.0,
            vram_total_mb=8192.0,
            power_draw_w=power_w,
            temperature_c=62.0,
        ),
        cpu_utilization_percent=12.5,
        system_memory_used_mb=4096.0,
        current_model=None,
        inference_engine=None,
        request_count=0,
        error_count=0,
    )


if __name__ == "__main__":
    unittest.main()
