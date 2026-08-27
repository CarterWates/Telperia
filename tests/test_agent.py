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

    def test_agent_privacy_mode_defaults_are_private_and_local_only(self) -> None:
        from telperia_agent.privacy import resolve_privacy_settings

        settings = resolve_privacy_settings()

        self.assertEqual(settings.mode, "private")
        self.assertEqual(settings.upload_policy, "disabled")
        self.assertFalse(settings.upload_enabled)
        self.assertFalse(settings.research_contribution_enabled)
        self.assertEqual(settings.status, "active")
        self.assert_public_safe(settings.to_dict())

    def test_agent_planned_cloud_modes_are_recognized_but_block_upload(self) -> None:
        from telperia_agent.privacy import resolve_privacy_settings

        personal = resolve_privacy_settings("personal_cloud")
        research = resolve_privacy_settings("research_contribution", research_contribution_enabled=True)

        self.assertEqual(personal.mode, "personal_cloud")
        self.assertEqual(personal.status, "planned_not_connected")
        self.assertFalse(personal.upload_enabled)
        self.assertEqual(personal.upload_policy, "blocked_until_backend_available")
        self.assertFalse(personal.research_contribution_enabled)
        self.assertEqual(research.mode, "research_contribution")
        self.assertEqual(research.status, "planned_not_connected")
        self.assertFalse(research.upload_enabled)
        self.assertTrue(research.research_contribution_enabled)
        self.assert_public_safe(personal.to_dict())
        self.assert_public_safe(research.to_dict())

    def test_agent_research_contribution_requires_explicit_opt_in(self) -> None:
        from telperia_agent.privacy import PrivacyModeError, resolve_privacy_settings

        with self.assertRaisesRegex(PrivacyModeError, "explicit opt-in"):
            resolve_privacy_settings("research_contribution")

    def test_agent_privacy_status_reports_private_mode_and_no_upload(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(AGENT_CLI_PATH), "privacy-status"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "private")
        self.assertEqual(payload["status"], "active")
        self.assertFalse(payload["upload_enabled"])
        self.assertFalse(payload["research_contribution_enabled"])
        self.assert_public_safe(payload)

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
                    "--privacy-mode",
                    "private",
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
            record = json.loads(lines[0])
            event = record["data"]
            self.assertEqual(record["record_type"], "inference_event")
            self.assertEqual(record["privacy"]["mode"], "private")
            self.assertFalse(record["privacy"]["upload_enabled"])
            validate_result_package(event, SCHEMA_PATH)
            self.assert_public_safe(record)

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
                    "--privacy-mode",
                    "private",
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
        self.assertEqual(records[0]["privacy"]["mode"], "private")
        self.assertFalse(records[0]["privacy"]["upload_enabled"])
        self.assertEqual(records[2]["data"]["inference_engine"], "ollama")
        self.assertIn("upload disabled", completed.stdout.lower())
        for record in records:
            self.assert_public_safe(record)

    def test_agent_blocks_planned_upload_modes_for_local_exports(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "events.jsonl"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(AGENT_CLI_PATH),
                    "record-once",
                    "--output",
                    str(output),
                    "--model-id",
                    "llama3.1:8b",
                    "--latency-ms",
                    "250",
                    "--input-tokens",
                    "12",
                    "--output-tokens",
                    "18",
                    "--privacy-mode",
                    "personal-cloud",
                ],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("not connected", completed.stderr.lower())
            self.assertFalse(output.exists())

    def test_agent_runtime_loop_writes_buffered_private_records(self) -> None:
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(AGENT_CLI_PATH),
                    "run",
                    "--output-dir",
                    str(output_dir),
                    "--interval-seconds",
                    "0",
                    "--max-samples",
                    "2",
                    "--model-id",
                    "llama3.1:8b",
                    "--inference-engine",
                    "ollama",
                ],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("2 sample", completed.stdout.lower())
            records = self.read_buffer_records(output_dir)

        self.assertEqual(len(records), 2)
        self.assertTrue(all(record["record_type"] == "hardware_sample" for record in records))
        self.assertTrue(all(record["privacy"]["mode"] == "private" for record in records))
        self.assertTrue(all(record["buffer"]["upload_status"] == "not_configured" for record in records))
        self.assertTrue(all(record["buffer"]["upload_attempt_count"] == 0 for record in records))
        self.assertEqual(len({record["buffer"]["local_record_id"] for record in records}), 2)
        for record in records:
            validate_result_package(record["data"], TELEMETRY_SCHEMA_PATH)
            self.assert_public_safe(record)

    def test_agent_runtime_storage_limit_is_enforced_safely(self) -> None:
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(AGENT_CLI_PATH),
                    "run",
                    "--output-dir",
                    str(output_dir),
                    "--interval-seconds",
                    "0",
                    "--max-samples",
                    "1",
                    "--max-storage-bytes",
                    "1",
                    "--model-id",
                    "llama3.1:8b",
                ],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("storage limit", completed.stderr.lower())
            self.assertEqual(self.read_buffer_records(output_dir), [])

    def test_agent_buffer_identifies_duplicate_records_by_hash(self) -> None:
        from telperia_agent.buffer import AgentBuffer
        from telperia_agent.privacy import resolve_privacy_settings

        with TemporaryDirectory() as directory:
            agent_buffer = AgentBuffer(Path(directory))
            settings = resolve_privacy_settings()
            data = {
                "request_id": "request-1",
                "start_time": "2026-08-26T12:00:00Z",
                "end_time": "2026-08-26T12:00:01Z",
                "latency_ms": 1000.0,
                "model_id": "llama3.1:8b",
                "input_tokens": 1,
                "output_tokens": 2,
                "tokens_per_second": 2.0,
                "success": True,
                "error_category": None,
            }

            first = agent_buffer.append("inference_event", data, settings)
            second = agent_buffer.append("inference_event", data, settings)
            records = agent_buffer.read_records()

        self.assertEqual(first["buffer"]["content_hash"], second["buffer"]["content_hash"])
        self.assertEqual(first["buffer"]["local_record_id"], second["buffer"]["local_record_id"])
        self.assertTrue(second["buffer"]["duplicate"])
        self.assertEqual(len(records), 1)

    def test_agent_buffer_status_lists_pending_records_without_private_fields(self) -> None:
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            self.run_agent(
                "run",
                "--output-dir",
                str(output_dir),
                "--interval-seconds",
                "0",
                "--max-samples",
                "1",
                "--model-id",
                "llama3.1:8b",
            )

            completed = self.run_agent("buffer-status", "--output-dir", str(output_dir))
            payload = json.loads(completed.stdout)

        self.assertEqual(payload["pending_count"], 1)
        self.assertEqual(payload["upload_status"], "not_configured")
        self.assertEqual(payload["privacy_mode"], "private")
        self.assert_public_safe(payload)

    def test_agent_delete_local_data_removes_only_agent_owned_files(self) -> None:
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            unrelated = output_dir / "notes.txt"
            unrelated.write_text("keep me", encoding="utf-8")
            self.run_agent(
                "run",
                "--output-dir",
                str(output_dir),
                "--interval-seconds",
                "0",
                "--max-samples",
                "1",
                "--model-id",
                "llama3.1:8b",
            )
            self.run_agent("pause", "--output-dir", str(output_dir))

            completed = self.run_agent("delete-local-data", "--output-dir", str(output_dir), "--confirm")

            self.assertIn("deleted", completed.stdout.lower())
            self.assertTrue(unrelated.exists())
            self.assertEqual(self.read_buffer_records(output_dir), [])
            self.assertFalse((output_dir / "agent-state.json").exists())

    def test_agent_pause_prevents_collection_and_resume_allows_collection(self) -> None:
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            self.run_agent("pause", "--output-dir", str(output_dir))

            paused = self.run_agent(
                "run",
                "--output-dir",
                str(output_dir),
                "--interval-seconds",
                "0",
                "--max-samples",
                "1",
                "--model-id",
                "llama3.1:8b",
            )
            self.assertIn("paused", paused.stdout.lower())
            self.assertEqual(self.read_buffer_records(output_dir), [])

            self.run_agent("resume", "--output-dir", str(output_dir))
            resumed = self.run_agent(
                "run",
                "--output-dir",
                str(output_dir),
                "--interval-seconds",
                "0",
                "--max-samples",
                "1",
                "--model-id",
                "llama3.1:8b",
            )
            records_after_resume = self.read_buffer_records(output_dir)

        self.assertIn("1 sample", resumed.stdout.lower())
        self.assertEqual(len(records_after_resume), 1)

    def test_agent_collected_fields_lists_allowed_fields_and_excludes_private_fields(self) -> None:
        completed = self.run_agent("collected-fields")
        payload = json.loads(completed.stdout)

        self.assertIn("gpu.utilization_percent", payload["hardware"])
        self.assertIn("model_id", payload["inference"])
        self.assertIn("operating_system", payload["environment"])
        self.assertIn("privacy.mode", payload["local_metadata"])
        self.assertIn("prompt", payload["never_collected"])
        self.assertIn("response", payload["never_collected"])
        self.assertNotIn("prompt", payload["hardware"])
        self.assertNotIn("response", payload["inference"])
        self.assert_public_safe({"allowed": payload["hardware"] + payload["inference"] + payload["environment"] + payload["local_metadata"]})

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

    def run_agent(self, *args: str) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(AGENT_CLI_PATH), *args],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed

    def read_buffer_records(self, output_dir: Path) -> list[dict]:
        buffer_path = output_dir / "agent-buffer.jsonl"
        if not buffer_path.exists():
            return []
        return [json.loads(line) for line in buffer_path.read_text(encoding="utf-8").splitlines()]


if __name__ == "__main__":
    unittest.main()
