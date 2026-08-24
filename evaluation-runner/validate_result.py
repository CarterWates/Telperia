#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = PROJECT_ROOT / "apps" / "api"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "evaluation-run.schema.json"

sys.path.insert(0, str(API_ROOT))

from telperia_api.ingestion_service import InMemoryIngestionStore, ingest_result_request


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Telperia result package locally.")
    parser.add_argument("result_path", type=Path, help="Path to a Telperia result package JSON file.")
    parser.add_argument(
        "--submit-for-public-review",
        action="store_true",
        help="Validate using the public-review submission mode. No upload is performed.",
    )
    parser.add_argument(
        "--user-id",
        default="local-cli-user",
        help="Local authenticated user placeholder for backend-shaped validation.",
    )
    args = parser.parse_args()

    try:
        package = json.loads(args.result_path.read_text())
    except OSError as exc:
        parser.exit(status=2, message=f"unable to read result package: {exc}\n")
    except json.JSONDecodeError as exc:
        parser.exit(status=2, message=f"invalid JSON: {exc}\n")

    visibility = "submit_for_public_review" if args.submit_for_public_review else "private"
    response = ingest_result_request(
        {"result_package": package, "visibility": visibility},
        user_id=args.user_id,
        schema_path=SCHEMA_PATH,
        store=InMemoryIngestionStore(),
    )
    print(json.dumps(response.payload, indent=2))
    return 0 if response.status_code in {200, 201} else 1


if __name__ == "__main__":
    raise SystemExit(main())
