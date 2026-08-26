from __future__ import annotations

import importlib
import json
import subprocess
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "agent"
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "inference-event.schema.json"
TELEMETRY_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "telemetry-sample.schema.json"
AGENT_CLI_PATH = AGENT_ROOT / "agent.py"

sys.path.insert(0, str(AGENT_ROOT))
sys.path.insert(0, str(RUNNER_ROOT))

from telperia_runner.schema import validate_result_package


PRIVATE_FIELD_NAMES = {
    "prompt",
    "prompt_text",
    "response",
    "response_text",
    "content",
    "filename",
    "file_path",
    "environment",
    "env",
    "api_key",
    "token",
    "password",
    "secret",
    "hostname",
    "serial_number",
    "username",
}


class TelperiaAgentTests(unittest.TestCase):
    def test_agent_package_and_entrypoint_exist(self) -> None:
        agent_module = importlib.import_module("telperia_agent")

        self.assertTrue(AGENT_CLI_PATH.exists())
        self.assertEqual(agent_module.DEFAULT_MODE, "private")

    def test_builds_schema_valid_non_content_event(self) -> None:
        from telperia_agent.events import build_inference_event

        event = build_inference_event(
            request_id="request-1",
            model_id="llama3.1:8b",
            latency_ms=250.0,
            input_tokens=12,
            output_tokens=18,
            success=True,
        )

        validate_result_package(event, SCHEMA_PATH)
        self.assertEqual(event["request_id"], "request-1")
        self.assertEqual(event["model_id"], "llama3.1:8b")
        self.assertEqual(event["tokens_per_second"], 72.0)
        self.assertIsNone(event["error_category"])
        self.assert_public_safe(event)

    def test_agent_exports_local_jsonl_without_uploading(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "events.jsonl"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(AGENT_CLI_PATH),
                    "record-once",
                    "--output",
                    str(output),
                    "--request-id",
                    "request-1",
                    "--model-id",
                    "llama3.1:8b",
                    "--latency-ms",
                    "250",
                    "--input-tokens",
                    "12",
                    "--output-tokens",
                    "18",
                ],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("upload disabled", completed.stdout.lower())
            lines = output.read_text().splitlines()
            self.assertEqual(len(lines), 1)
            event = json.loads(lines[0])
            validate_result_package(event, SCHEMA_PATH)
            self.assert_public_safe(event)

    def test_agent_builds_schema_valid_hardware_record_from_shared_telemetry(self) -> None:
        from telperia_agent.hardware import build_hardware_sample
        from telperia_agent.telemetry import GpuMetrics, TelemetrySample

        sample = build_hardware_sample(
            node_id="local",
            gpu=GpuMetrics(
                index=0,
                name="NVIDIA GeForce RTX 5070",
                utilization_percent=42.5,
                vram_used_mb=2048.0,
                vram_total_mb=12288.0,
                power_draw_w=88.0,
                temperature_c=61.0,
            ),
            cpu_utilization_percent=12.0,
            system_memory_used_mb=8192.0,
            current_model="llama3.1:8b",
            inference_engine="ollama",
            request_count=3,
            error_count=1,
            timestamp=datetime(2026, 8, 26, 12, 0, tzinfo=UTC),
        )

        self.assertIsInstance(sample, TelemetrySample)
        payload = sample.to_dict()
        validate_result_package(payload, TELEMETRY_SCHEMA_PATH)
        self.assertEqual(payload["gpu"]["utilization_percent"], 42.5)
        self.assertEqual(payload["gpu"]["vram_used_mb"], 2048.0)
        self.assertEqual(payload["gpu"]["power_draw_w"], 88.0)
        self.assertEqual(payload["gpu"]["temperature_c"], 61.0)
        self.assertEqual(payload["cpu_utilization_percent"], 12.0)
        self.assertEqual(payload["system_memory_used_mb"], 8192.0)
        self.assert_public_safe(payload)

    def test_agent_represents_unavailable_hardware_telemetry_honestly(self) -> None:
        from telperia_agent.hardware import build_unavailable_hardware_sample

        payload = build_unavailable_hardware_sample(
            node_id="local",
            current_model=None,
            inference_engine="ollama",
            timestamp=datetime(2026, 8, 26, 12, 0, tzinfo=UTC),
        ).to_dict()

        validate_result_package(payload, TELEMETRY_SCHEMA_PATH)
        self.assertEqual(payload["gpu"]["name"], "unavailable")
        self.assertEqual(payload["gpu"]["utilization_percent"], 0.0)
        self.assertEqual(payload["gpu"]["power_draw_w"], 0.0)
        self.assertEqual(payload["current_model"], None)
        self.assert_public_safe(payload)

    def test_agent_builds_environment_metadata_without_private_machine_ids(self) -> None:
        from telperia_agent.environment import build_environment_metadata

        metadata = build_environment_metadata(
            operating_system="Darwin",
            gpu_model="unavailable",
            driver_version="unknown",
            cuda_version="unavailable",
            inference_engine="ollama",
            runtime_version="0.3.12",
            quantization="q4_K_M",
        )

        self.assertEqual(metadata["record_type"], "environment")
        self.assertEqual(metadata["operating_system"], "Darwin")
        self.assertEqual(metadata["gpu_model"], "unavailable")
        self.assertEqual(metadata["driver_version"], "unknown")
        self.assertEqual(metadata["cuda_version"], "unavailable")
        self.assertEqual(metadata["inference_engine"], "ollama")
        self.assertEqual(metadata["runtime_version"], "0.3.12")
        self.assertEqual(metadata["quantization"], "q4_K_M")
        self.assert_public_safe(metadata)

    def test_agent_snapshot_exports_inference_hardware_and_environment_records(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.jsonl"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(AGENT_CLI_PATH),
                    "snapshot",
                    "--output",
                    str(output),
                    "--request-id",
                    "request-1",
                    "--model-id",
                    "llama3.1:8b",
                    "--latency-ms",
                    "250",
                    "--input-tokens",
                    "12",
                    "--output-tokens",
                    "18",
                    "--inference-engine",
                    "ollama",
                    "--runtime-version",
                    "0.3.12",
                    "--quantization",
                    "q4_K_M",
                ],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            records = [json.loads(line) for line in output.read_text().splitlines()]

        self.assertEqual([record["record_type"] for record in records], ["inference_event", "hardware_sample", "environment"])
        validate_result_package(records[0]["data"], SCHEMA_PATH)
        validate_result_package(records[1]["data"], TELEMETRY_SCHEMA_PATH)
        self.assertEqual(records[2]["data"]["inference_engine"], "ollama")
        self.assertIn("upload disabled", completed.stdout.lower())
        for record in records:
            self.assert_public_safe(record)

    def test_agent_rejects_private_content_fields_before_export(self) -> None:
        from telperia_agent.events import build_inference_event

        with self.assertRaisesRegex(ValueError, "private content"):
            build_inference_event(
                request_id="request-1",
                model_id="llama3.1:8b",
                latency_ms=250.0,
                input_tokens=12,
                output_tokens=18,
                success=True,
                extra_fields={"prompt": "do not collect this"},
            )

    def test_agent_reuses_shared_telemetry_package_without_importing_runner_evaluator(self) -> None:
        agent_telemetry = importlib.import_module("telperia_agent.telemetry")
        telemetry_models = importlib.import_module("telperia_telemetry.models")
        agent_source = (AGENT_ROOT / "telperia_agent" / "telemetry.py").read_text()

        self.assertIs(agent_telemetry.TelemetrySample, telemetry_models.TelemetrySample)
        self.assertNotIn("telperia_runner.evaluator", agent_source)

    def test_evaluation_runner_imports_still_work(self) -> None:
        evaluator = importlib.import_module("telperia_runner.evaluator")
        suite = importlib.import_module("telperia_runner.suite")

        self.assertTrue(hasattr(evaluator, "run_evaluation"))
        self.assertTrue(hasattr(suite, "load_suite"))

    def assert_public_safe(self, payload: dict) -> None:
        def walk(value: object) -> None:
            if isinstance(value, dict):
                lowered_keys = {str(key).lower() for key in value}
                self.assertTrue(PRIVATE_FIELD_NAMES.isdisjoint(lowered_keys))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(payload)


if __name__ == "__main__":
    unittest.main()
