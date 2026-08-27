from __future__ import annotations

import argparse
import json
import sys
from time import sleep
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from telperia_agent import DEFAULT_MODE, DEFAULT_RESEARCH_CONTRIBUTION_ENABLED, DEFAULT_UPLOAD_ENABLED
from telperia_agent.buffer import AgentBuffer, BufferLimitError
from telperia_agent.environment import build_environment_metadata
from telperia_agent.events import build_inference_event
from telperia_agent.exporters import append_jsonl
from telperia_agent.fields import collected_fields_manifest
from telperia_agent.hardware import build_unavailable_hardware_sample
from telperia_agent.privacy import (
    PrivacyModeError,
    require_local_export_allowed,
    resolve_privacy_settings,
    wrap_local_record,
)
from telperia_runner.schema import SchemaValidationError, validate_result_package


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local Telperia Agent stub.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    privacy_status = subcommands.add_parser(
        "privacy-status",
        help="Show current local Agent privacy mode settings.",
    )
    _add_privacy_arguments(privacy_status)

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
    _add_privacy_arguments(record_once)

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
    _add_privacy_arguments(snapshot)

    run = subcommands.add_parser(
        "run",
        help="Run the local Agent loop and buffer non-content hardware records.",
    )
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--interval-seconds", type=float, default=5.0)
    run.add_argument("--max-samples", type=int)
    run.add_argument("--max-storage-bytes", type=int, default=5_000_000)
    run.add_argument("--model-id")
    run.add_argument("--inference-engine", default="unknown")
    run.add_argument(
        "--telemetry-schema",
        type=Path,
        default=PROJECT_ROOT / "schemas" / "telemetry-sample.schema.json",
        help="Path to schemas/telemetry-sample.schema.json.",
    )
    _add_privacy_arguments(run)

    buffer_status = subcommands.add_parser(
        "buffer-status",
        help="Show local Agent buffer status without reading raw private content.",
    )
    buffer_status.add_argument("--output-dir", type=Path, required=True)

    delete_local_data = subcommands.add_parser(
        "delete-local-data",
        help="Delete Agent-owned local buffer and pause state files.",
    )
    delete_local_data.add_argument("--output-dir", type=Path, required=True)
    delete_local_data.add_argument("--confirm", action="store_true")

    pause = subcommands.add_parser("pause", help="Pause local Agent collection.")
    pause.add_argument("--output-dir", type=Path, required=True)

    resume = subcommands.add_parser("resume", help="Resume local Agent collection.")
    resume.add_argument("--output-dir", type=Path, required=True)

    subcommands.add_parser(
        "collected-fields",
        help="Show exactly which Agent fields are collected and which are never collected.",
    )

    args = parser.parse_args()
    if args.command == "privacy-status":
        return _privacy_status(args)
    if args.command == "record-once":
        return _record_once(args)
    if args.command == "snapshot":
        return _snapshot(args)
    if args.command == "run":
        return _run(args)
    if args.command == "buffer-status":
        return _buffer_status(args)
    if args.command == "delete-local-data":
        return _delete_local_data(args)
    if args.command == "pause":
        return _pause(args)
    if args.command == "resume":
        return _resume(args)
    if args.command == "collected-fields":
        return _collected_fields()
    return 2


def _add_privacy_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--privacy-mode",
        choices=["private", "personal-cloud", "personal_cloud", "research-contribution", "research_contribution"],
        default="private",
        help="Agent privacy mode. Only private mode is active in the MVP.",
    )
    parser.add_argument(
        "--research-contribution-opt-in",
        action="store_true",
        help="Explicitly acknowledge Research Contribution Mode. Upload is still disabled.",
    )


def _privacy_status(args: argparse.Namespace) -> int:
    try:
        settings = resolve_privacy_settings(
            args.privacy_mode,
            research_contribution_enabled=args.research_contribution_opt_in,
        )
    except PrivacyModeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(settings.to_dict(), sort_keys=True), flush=True)
    return 0


def _record_once(args: argparse.Namespace) -> int:
    try:
        privacy_settings = resolve_privacy_settings(
            args.privacy_mode,
            research_contribution_enabled=args.research_contribution_opt_in,
        )
        require_local_export_allowed(privacy_settings)
    except PrivacyModeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

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

    append_jsonl(wrap_local_record("inference_event", event, privacy_settings), args.output)
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
    try:
        privacy_settings = resolve_privacy_settings(
            args.privacy_mode,
            research_contribution_enabled=args.research_contribution_opt_in,
        )
        require_local_export_allowed(privacy_settings)
    except PrivacyModeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

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

    append_jsonl(wrap_local_record("inference_event", event, privacy_settings), args.output)
    append_jsonl(
        wrap_local_record("hardware_sample", hardware_sample.to_dict(), privacy_settings),
        args.output,
    )
    append_jsonl(wrap_local_record("environment", environment, privacy_settings), args.output)
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


def _run(args: argparse.Namespace) -> int:
    if args.interval_seconds < 0:
        print("interval-seconds must be nonnegative.", file=sys.stderr)
        return 2
    if args.max_samples is not None and args.max_samples < 1:
        print("max-samples must be positive when provided.", file=sys.stderr)
        return 2
    try:
        privacy_settings = resolve_privacy_settings(
            args.privacy_mode,
            research_contribution_enabled=args.research_contribution_opt_in,
        )
        require_local_export_allowed(privacy_settings)
    except PrivacyModeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    agent_buffer = AgentBuffer(args.output_dir)
    if agent_buffer.is_paused():
        print("Agent collection is paused; no records written.", flush=True)
        return 0

    written = 0
    try:
        while args.max_samples is None or written < args.max_samples:
            sample = build_unavailable_hardware_sample(
                node_id="local",
                current_model=args.model_id,
                inference_engine=args.inference_engine,
                request_count=0,
                error_count=0,
            )
            try:
                validate_result_package(sample.to_dict(), args.telemetry_schema)
                agent_buffer.append(
                    "hardware_sample",
                    sample.to_dict(),
                    privacy_settings,
                    max_storage_bytes=args.max_storage_bytes,
                )
            except SchemaValidationError as exc:
                print(f"Invalid hardware sample: {exc}", file=sys.stderr)
                return 1
            except BufferLimitError as exc:
                print(f"Local storage limit reached: {exc}", file=sys.stderr)
                return 1
            written += 1
            if args.max_samples is None or written < args.max_samples:
                sleep(args.interval_seconds)
    except KeyboardInterrupt:
        print(f"Agent stopped cleanly after {written} sample(s).", flush=True)
        return 0

    print(f"Agent wrote {written} sample(s) to the local buffer; upload disabled.", flush=True)
    return 0


def _buffer_status(args: argparse.Namespace) -> int:
    print(json.dumps(AgentBuffer(args.output_dir).status(), sort_keys=True), flush=True)
    return 0


def _delete_local_data(args: argparse.Namespace) -> int:
    if not args.confirm:
        print("delete-local-data requires --confirm.", file=sys.stderr)
        return 2
    deleted = AgentBuffer(args.output_dir).delete_local_data()
    print(f"Deleted {deleted} Agent-owned local file(s).", flush=True)
    return 0


def _pause(args: argparse.Namespace) -> int:
    AgentBuffer(args.output_dir).pause()
    print("Agent collection paused.", flush=True)
    return 0


def _resume(args: argparse.Namespace) -> int:
    AgentBuffer(args.output_dir).resume()
    print("Agent collection resumed.", flush=True)
    return 0


def _collected_fields() -> int:
    print(json.dumps(collected_fields_manifest(), sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
