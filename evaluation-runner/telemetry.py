#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from telperia_telemetry.errors import TelemetryUnavailableError
from telperia_telemetry.exporters import write_csv, write_json
from telperia_telemetry.runner import collect_telemetry


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect local NVIDIA GPU telemetry.")
    parser.add_argument("--duration", type=int, required=True, help="Collection duration in seconds.")
    parser.add_argument("--output", type=Path, required=True, help="Output path ending in .json or .csv.")
    parser.add_argument("--node-id", default="local", help="Local node identifier.")
    parser.add_argument("--interval", type=float, default=1.0, help="Sampling interval in seconds.")
    parser.add_argument("--current-model", default=None, help="Current model identifier, if known.")
    parser.add_argument("--inference-engine", default=None, help="Inference engine, if known.")
    args = parser.parse_args()

    try:
        run = collect_telemetry(
            duration_s=args.duration,
            interval_s=args.interval,
            node_id=args.node_id,
            current_model=args.current_model,
            inference_engine=args.inference_engine,
        )
    except TelemetryUnavailableError as exc:
        parser.exit(status=2, message=f"telemetry unavailable: {exc}\n")

    if args.output.suffix.lower() == ".json":
        write_json(run, args.output)
    elif args.output.suffix.lower() == ".csv":
        write_csv(run, args.output)
    else:
        parser.exit(status=2, message="output must end in .json or .csv\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
