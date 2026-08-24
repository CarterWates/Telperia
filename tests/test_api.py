from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import UUID


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
API_ROOT = PROJECT_ROOT / "apps" / "api"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "ingestion"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "evaluation-run.schema.json"
VALIDATE_CLI_PATH = RUNNER_ROOT / "validate_result.py"

sys.path.insert(0, str(RUNNER_ROOT))
sys.path.insert(0, str(API_ROOT))

from telperia_api.ingestion_service import (
    InMemoryIngestionStore,
    canonical_package_hash,
    ingest_result_request,
    storage_path_for,
)


class LocalIngestionApiTests(unittest.TestCase):
    def test_canonical_package_hash_is_stable_across_key_order(self) -> None:
        left = {"b": 2, "a": {"d": 4, "c": 3}}
        right = {"a": {"c": 3, "d": 4}, "b": 2}

        self.assertEqual(canonical_package_hash(left), canonical_package_hash(right))

    def test_storage_path_is_generated_from_user_and_run_id(self) -> None:
        path = storage_path_for(user_id="user-1", run_id="run-1")

        self.assertEqual(path, "result-packages/users/user-1/runs/run-1.json")

    def test_accepts_private_upload_and_stores_local_record(self) -> None:
        package = load_fixture("valid_private_upload.json")
        store = InMemoryIngestionStore()

        response = ingest_result_request(
            {"result_package": package},
            user_id="user-1",
            schema_path=SCHEMA_PATH,
            store=store,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.payload["ingestion_status"], "accepted")
        self.assertEqual(response.payload["visibility"], "private")
        self.assertEqual(response.payload["run_id"], package["run_id"])
        UUID(response.payload["upload_id"])

        record = store.get_by_run_id(package["run_id"])
        self.assertIsNotNone(record)
        self.assertEqual(record.storage_path, f"result-packages/users/user-1/runs/{package['run_id']}.json")
        self.assertEqual(record.observatory_summary["model_name"], package["model"]["name"])

    def test_accepts_public_review_request_as_pending_review(self) -> None:
        package = load_fixture("valid_private_upload.json")

        response = ingest_result_request(
            {"result_package": package, "visibility": "submit_for_public_review"},
            user_id="user-1",
            schema_path=SCHEMA_PATH,
            store=InMemoryIngestionStore(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.payload["visibility"], "submitted_for_public_review")
        self.assertEqual(response.payload["public_submission_status"], "pending_review")

    def test_rejects_direct_public_visibility(self) -> None:
        package = load_fixture("valid_private_upload.json")

        response = ingest_result_request(
            {"result_package": package, "visibility": "public"},
            user_id="user-1",
            schema_path=SCHEMA_PATH,
            store=InMemoryIngestionStore(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.payload["error_code"], "invalid_visibility")

    def test_rejects_unauthenticated_upload(self) -> None:
        package = load_fixture("valid_private_upload.json")

        response = ingest_result_request(
            {"result_package": package},
            user_id="",
            schema_path=SCHEMA_PATH,
            store=InMemoryIngestionStore(),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.payload["error_code"], "unauthenticated")

    def test_returns_existing_record_for_duplicate_matching_package(self) -> None:
        package = load_fixture("valid_private_upload.json")
        store = InMemoryIngestionStore()

        first = ingest_result_request({"result_package": package}, user_id="user-1", schema_path=SCHEMA_PATH, store=store)
        second = ingest_result_request({"result_package": package}, user_id="user-1", schema_path=SCHEMA_PATH, store=store)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.payload["duplicate"])
        self.assertEqual(second.payload["upload_id"], first.payload["upload_id"])

    def test_rejects_duplicate_run_id_with_different_content(self) -> None:
        package = load_fixture("duplicate_run_id_original.json")
        changed_package = load_fixture("duplicate_run_id_changed.json")
        store = InMemoryIngestionStore()

        first = ingest_result_request({"result_package": package}, user_id="user-1", schema_path=SCHEMA_PATH, store=store)
        second = ingest_result_request(
            {"result_package": changed_package},
            user_id="user-1",
            schema_path=SCHEMA_PATH,
            store=store,
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.payload["error_code"], "duplicate_run_id")

    def test_rejects_invalid_result_package_without_storing_record(self) -> None:
        package = load_fixture("valid_private_upload.json")
        package["evaluation"]["scores"]["private_probe"] = {"prompt": "do not store me"}
        store = InMemoryIngestionStore()

        response = ingest_result_request({"result_package": package}, user_id="user-1", schema_path=SCHEMA_PATH, store=store)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.payload["error_code"], "privacy_violation")
        self.assertIsNone(store.get_by_run_id(package["run_id"]))


class ValidateResultCliTests(unittest.TestCase):
    def test_cli_accepts_valid_result_file(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATE_CLI_PATH),
                str(FIXTURE_ROOT / "valid_private_upload.json"),
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["ingestion_status"], "accepted")
        self.assertEqual(payload["visibility"], "private")

    def test_cli_accepts_public_review_mode(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATE_CLI_PATH),
                str(FIXTURE_ROOT / "valid_private_upload.json"),
                "--submit-for-public-review",
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["visibility"], "submitted_for_public_review")
        self.assertEqual(payload["public_submission_status"], "pending_review")

    def test_cli_rejects_invalid_result_file(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATE_CLI_PATH),
                str(FIXTURE_ROOT / "rejected_prompt_response_content.json"),
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["ingestion_status"], "rejected")
        self.assertEqual(payload["error_code"], "privacy_violation")


def load_fixture(filename: str) -> dict:
    return json.loads((FIXTURE_ROOT / filename).read_text())


if __name__ == "__main__":
    unittest.main()
