from __future__ import annotations

import importlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "agent"
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "inference-event.schema.json"
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
        serialized = json.dumps(payload).lower()
        self.assertTrue(PRIVATE_FIELD_NAMES.isdisjoint(payload))
        for private_name in PRIVATE_FIELD_NAMES:
            self.assertNotIn(f'"{private_name}"', serialized)


if __name__ == "__main__":
    unittest.main()
