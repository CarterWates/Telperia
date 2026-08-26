from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from telperia_agent import DEFAULT_MODE, DEFAULT_RESEARCH_CONTRIBUTION_ENABLED, DEFAULT_UPLOAD_ENABLED
from telperia_agent.environment import build_environment_metadata
from telperia_agent.events import build_inference_event
from telperia_agent.exporters import append_jsonl
from telperia_agent.hardware import build_unavailable_hardware_sample, hardware_sample_record
from telperia_runner.schema import SchemaValidationError, validate_result_package


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local Telperia Agent stub.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    record_once = subcommands.add_parser(
        "record-once",
        help="Write one non-content inference event to a local JSONL file.",
    )
    record_once.add_argument("--output", type=Path, required=True)
    record_once.add_argument("--request-id")
    record_once.add_argument("--model-id", required=True)
    record_once.add_argument("--latency-ms", type=float, required=True)
    record_once.add_argument("--input-tokens", type=int, required=True)
    record_once.add_argument("--output-tokens", type=int, required=True)
    record_once.add_argument("--success", action=argparse.BooleanOptionalAction, default=True)
    record_once.add_argument("--error-category")
    record_once.add_argument(
        "--schema",
        type=Path,
        default=PROJECT_ROOT / "schemas" / "inference-event.schema.json",
        help="Path to schemas/inference-event.schema.json.",
    )

    snapshot = subcommands.add_parser(
        "snapshot",
        help="Write one local Agent v0.1 inference, hardware, and environment snapshot.",
    )
    snapshot.add_argument("--output", type=Path, required=True)
    snapshot.add_argument("--request-id")
    snapshot.add_argument("--model-id", required=True)
    snapshot.add_argument("--latency-ms", type=float, required=True)
    snapshot.add_argument("--input-tokens", type=int, required=True)
    snapshot.add_argument("--output-tokens", type=int, required=True)
    snapshot.add_argument("--success", action=argparse.BooleanOptionalAction, default=True)
    snapshot.add_argument("--error-category")
    snapshot.add_argument("--inference-engine", default="unknown")
    snapshot.add_argument("--runtime-version", default="unknown")
    snapshot.add_argument("--quantization", default="unknown")
    snapshot.add_argument("--operating-system")
    snapshot.add_argument("--gpu-model", default="unavailable")
    snapshot.add_argument("--driver-version", default="unknown")
    snapshot.add_argument("--cuda-version", default="unavailable")
    snapshot.add_argument(
        "--schema",
        type=Path,
        default=PROJECT_ROOT / "schemas" / "inference-event.schema.json",
        help="Path to schemas/inference-event.schema.json.",
    )
    snapshot.add_argument(
        "--telemetry-schema",
        type=Path,
        default=PROJECT_ROOT / "schemas" / "telemetry-sample.schema.json",
        help="Path to schemas/telemetry-sample.schema.json.",
    )

    args = parser.parse_args()
    if args.command == "record-once":
        return _record_once(args)
    if args.command == "snapshot":
        return _snapshot(args)
    return 2


def _record_once(args: argparse.Namespace) -> int:
    event = build_inference_event(
        request_id=args.request_id,
        model_id=args.model_id,
        latency_ms=args.latency_ms,
        input_tokens=args.input_tokens,
        output_tokens=args.output_tokens,
        success=args.success,
        error_category=args.error_category,
    )
    try:
        validate_result_package(event, args.schema)
    except SchemaValidationError as exc:
        print(f"Invalid inference event: {exc}", file=sys.stderr)
        return 1

    append_jsonl(event, args.output)
    print(
        "Recorded one private/local-only inference event; upload disabled and research contribution disabled.",
        flush=True,
    )
    print(
        f"mode={DEFAULT_MODE} upload_enabled={DEFAULT_UPLOAD_ENABLED} "
        f"research_contribution_enabled={DEFAULT_RESEARCH_CONTRIBUTION_ENABLED}",
        flush=True,
    )
    return 0


def _snapshot(args: argparse.Namespace) -> int:
    event = build_inference_event(
        request_id=args.request_id,
        model_id=args.model_id,
        latency_ms=args.latency_ms,
        input_tokens=args.input_tokens,
        output_tokens=args.output_tokens,
        success=args.success,
        error_category=args.error_category,
    )
    hardware_sample = build_unavailable_hardware_sample(
        node_id="local",
        current_model=args.model_id,
        inference_engine=args.inference_engine,
        request_count=1,
        error_count=0 if args.success else 1,
    )
    environment = build_environment_metadata(
        operating_system=args.operating_system,
        gpu_model=args.gpu_model,
        driver_version=args.driver_version,
        cuda_version=args.cuda_version,
        inference_engine=args.inference_engine,
        runtime_version=args.runtime_version,
        quantization=args.quantization,
    )

    try:
        validate_result_package(event, args.schema)
        validate_result_package(hardware_sample.to_dict(), args.telemetry_schema)
    except SchemaValidationError as exc:
        print(f"Invalid agent snapshot: {exc}", file=sys.stderr)
        return 1

    append_jsonl({"record_type": "inference_event", "data": event}, args.output)
    append_jsonl(hardware_sample_record(hardware_sample), args.output)
    append_jsonl({"record_type": "environment", "data": environment}, args.output)
    print(
        "Recorded one private/local-only agent snapshot; upload disabled and research contribution disabled.",
        flush=True,
    )
    print(
        f"mode={DEFAULT_MODE} upload_enabled={DEFAULT_UPLOAD_ENABLED} "
        f"research_contribution_enabled={DEFAULT_RESEARCH_CONTRIBUTION_ENABLED}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
