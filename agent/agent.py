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
from telperia_agent.events import build_inference_event
from telperia_agent.exporters import append_jsonl
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

    args = parser.parse_args()
    if args.command == "record-once":
        return _record_once(args)
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


if __name__ == "__main__":
    raise SystemExit(main())
