#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from telperia_runner.evaluator import run_evaluation
from telperia_runner.monitor import create_monitor
from telperia_runner.ollama import OllamaClient
from telperia_runner.schema import SchemaValidationError, validate_result_package
from telperia_runner.suite import load_suite
from telperia_telemetry.errors import TelemetryUnavailableError


DEFAULT_SUITE = Path(__file__).resolve().parent / "suites" / "tci-v0.1.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "evaluation-run.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local Telperia evaluation.")
    parser.add_argument("--model", required=True, help="Ollama model name, for example llama3.1:8b.")
    parser.add_argument("--output", type=Path, required=True, help="Result package path.")
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE, help="Evaluation suite JSON path.")
    parser.add_argument("--provider", default="ollama", choices=["ollama"], help="Inference provider.")
    parser.add_argument(
        "--hardware-monitor",
        default="disabled",
        choices=["disabled", "nvml"],
        help="Hardware monitor to run during evaluation.",
    )
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434", help="Ollama base URL.")
    parser.add_argument("--model-revision", default="unknown", help="Model revision metadata.")
    parser.add_argument("--quantization", default="unknown", help="Model quantization metadata.")
    parser.add_argument("--max-output-tokens", type=int, default=64, help="Maximum generated tokens per task.")
    args = parser.parse_args()

    suite = load_suite(args.suite)
    client = OllamaClient(base_url=args.ollama_url)

    try:
        with create_monitor(args.hardware_monitor) as monitor:
            package = run_evaluation(
                suite=suite,
                model_name=args.model,
                client=client,
                hardware=monitor.hardware(),
                energy=monitor.energy,
                model_revision=args.model_revision,
                quantization=args.quantization,
                max_output_tokens=args.max_output_tokens,
            )
    except (ConnectionError, TelemetryUnavailableError) as exc:
        parser.exit(status=2, message=f"evaluation unavailable: {exc}\n")

    try:
        validate_result_package(package, SCHEMA_PATH)
    except SchemaValidationError as exc:
        parser.exit(status=2, message=f"invalid result package: {exc}\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(package, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
