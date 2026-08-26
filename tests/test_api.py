from __future__ import annotations

import json
import tempfile
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
from telperia_api.persistence import SQLiteIngestionStore


class LocalIngestionApiTests(unittest.TestCase):
    def test_canonical_package_hash_is_stable_across_key_order(self) -> None:
        left = {"b": 2, "a": {"d": 4, "c": 3}}
        right = {"a": {"c": 3, "d": 4}, "b": 2}

        self.assertEqual(canonical_package_hash(left), canonical_package_hash(right))

    def test_storage_path_is_generated_from_user_and_run_id(self) -> None:
        path = storage_path_for(user_id="user-1", run_id="run-1")

        self.assertEqual(path, "result-packages/users/user-1/runs/run-1.json")

    def test_storage_path_rejects_unsafe_segments(self) -> None:
        with self.assertRaises(ValueError):
            storage_path_for(user_id="../user-1", run_id="run-1")

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

    def test_rejects_unsafe_local_user_id(self) -> None:
        package = load_fixture("valid_private_upload.json")

        response = ingest_result_request(
            {"result_package": package},
            user_id="../user-1",
            schema_path=SCHEMA_PATH,
            store=InMemoryIngestionStore(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.payload["error_code"], "invalid_request_body")

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

    def test_rejects_cross_user_duplicate_run_id(self) -> None:
        package = load_fixture("valid_private_upload.json")
        store = InMemoryIngestionStore()

        first = ingest_result_request({"result_package": package}, user_id="user-1", schema_path=SCHEMA_PATH, store=store)
        second = ingest_result_request({"result_package": package}, user_id="user-2", schema_path=SCHEMA_PATH, store=store)

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


class SQLitePersistenceTests(unittest.TestCase):
    def test_persists_valid_private_upload_raw_package_and_summaries_separately(self) -> None:
        package = load_fixture("valid_private_upload.json")
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")

            response = ingest_result_request(
                {"result_package": package},
                user_id="user-1",
                schema_path=SCHEMA_PATH,
                store=store,
            )

            self.assertEqual(response.status_code, 201)
            upload_id = response.payload["upload_id"]
            self.assertEqual(store.raw_package_for_upload(upload_id), package)
            self.assertEqual(store.table_count("raw_result_packages"), 1)
            self.assertEqual(store.table_count("result_uploads"), 1)
            self.assertEqual(store.table_count("model_configs"), 1)
            self.assertEqual(store.table_count("hardware_profiles"), 1)
            self.assertEqual(store.table_count("evaluation_runs"), 1)
            self.assertEqual(store.table_count("run_scores"), 1)
            self.assertEqual(store.table_count("public_submissions"), 0)

            upload = store.upload_row_for_run(package["run_id"])
            self.assertEqual(upload["visibility"], "private")
            self.assertEqual(upload["ingestion_status"], "accepted")
            self.assertEqual(upload["schema_version"], "0.1")
            self.assertEqual(upload["methodology_version"], "0.1")

            summary = store.summary_row_for_run(package["run_id"])
            self.assertEqual(summary["model_name"], package["model"]["name"])
            self.assertEqual(summary["gpu"], package["hardware"]["gpu"])
            self.assertEqual(summary["tci_v0_1"], package["evaluation"]["scores"]["tci_v0_1"]["final_score"])
            self.assertNotIn("raw_results", summary)
            self.assertNotIn("prompt", json.dumps(summary).lower())
            self.assertNotIn("response", json.dumps(summary).lower())

    def test_persists_public_submission_request_as_pending_review(self) -> None:
        package = load_fixture("valid_private_upload.json")
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")

            response = ingest_result_request(
                {"result_package": package, "visibility": "submit_for_public_review"},
                user_id="user-1",
                schema_path=SCHEMA_PATH,
                store=store,
            )

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.payload["visibility"], "submitted_for_public_review")
            self.assertEqual(response.payload["public_submission_status"], "pending_review")
            self.assertEqual(store.table_count("public_submissions"), 1)
            upload = store.upload_row_for_run(package["run_id"])
            self.assertEqual(upload["visibility"], "submitted_for_public_review")
            self.assertEqual(upload["public_submission_requested"], 1)

    def test_rejected_uploads_do_not_persist_any_rows(self) -> None:
        invalid_schema = load_fixture("valid_private_upload.json")
        del invalid_schema["hardware"]
        privacy_violation = load_fixture("valid_private_upload.json")
        privacy_violation["evaluation"]["scores"]["private_probe"] = {"prompt": "do not store me"}

        for package in [invalid_schema, privacy_violation]:
            with tempfile.TemporaryDirectory() as directory:
                store = SQLiteIngestionStore(Path(directory) / "telperia.db")

                response = ingest_result_request(
                    {"result_package": package},
                    user_id="user-1",
                    schema_path=SCHEMA_PATH,
                    store=store,
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(store.table_count("raw_result_packages"), 0)
                self.assertEqual(store.table_count("result_uploads"), 0)
                self.assertEqual(store.table_count("evaluation_runs"), 0)
                self.assertEqual(store.table_count("run_scores"), 0)

    def test_direct_public_visibility_does_not_persist_rows(self) -> None:
        package = load_fixture("valid_private_upload.json")
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")

            response = ingest_result_request(
                {"result_package": package, "visibility": "public"},
                user_id="user-1",
                schema_path=SCHEMA_PATH,
                store=store,
            )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.payload["error_code"], "invalid_visibility")
            self.assertEqual(store.table_count("raw_result_packages"), 0)
            self.assertEqual(store.table_count("result_uploads"), 0)

    def test_missing_required_sections_are_rejected_before_persistence(self) -> None:
        for field in ["model", "runtime", "hardware", "methodology", "energy"]:
            package = load_fixture("valid_private_upload.json")
            del package[field]
            with tempfile.TemporaryDirectory() as directory:
                store = SQLiteIngestionStore(Path(directory) / "telperia.db")

                response = ingest_result_request(
                    {"result_package": package},
                    user_id="user-1",
                    schema_path=SCHEMA_PATH,
                    store=store,
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.payload["error_code"], "invalid_schema")
                self.assertEqual(store.table_count("raw_result_packages"), 0)
                self.assertEqual(store.table_count("result_uploads"), 0)

    def test_persisted_duplicate_handling_matches_contract(self) -> None:
        package = load_fixture("duplicate_run_id_original.json")
        changed_package = load_fixture("duplicate_run_id_changed.json")
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")

            first = ingest_result_request({"result_package": package}, user_id="user-1", schema_path=SCHEMA_PATH, store=store)
            same = ingest_result_request({"result_package": package}, user_id="user-1", schema_path=SCHEMA_PATH, store=store)
            changed = ingest_result_request(
                {"result_package": changed_package},
                user_id="user-1",
                schema_path=SCHEMA_PATH,
                store=store,
            )

            self.assertEqual(first.status_code, 201)
            self.assertEqual(same.status_code, 200)
            self.assertTrue(same.payload["duplicate"])
            self.assertEqual(changed.status_code, 409)
            self.assertEqual(changed.payload["error_code"], "duplicate_run_id")
            self.assertEqual(store.table_count("result_uploads"), 1)

    def test_persisted_cross_user_duplicate_run_id_is_rejected(self) -> None:
        package = load_fixture("valid_private_upload.json")
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")

            first = ingest_result_request({"result_package": package}, user_id="user-1", schema_path=SCHEMA_PATH, store=store)
            second = ingest_result_request({"result_package": package}, user_id="user-2", schema_path=SCHEMA_PATH, store=store)

            self.assertEqual(first.status_code, 201)
            self.assertEqual(second.status_code, 409)
            self.assertEqual(second.payload["error_code"], "duplicate_run_id")
            self.assertEqual(store.table_count("result_uploads"), 1)

    def test_public_results_list_returns_only_approved_public_summaries(self) -> None:
        package = load_fixture("valid_private_upload.json")
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")

            private_response = ingest_result_request(
                {"result_package": package},
                user_id="user-1",
                schema_path=SCHEMA_PATH,
                store=store,
            )
            self.assertEqual(private_response.status_code, 201)
            self.assertEqual(store.list_public_results(), [])

            public_package = load_fixture("duplicate_run_id_changed.json")
            public_response = ingest_result_request(
                {"result_package": public_package, "visibility": "submit_for_public_review"},
                user_id="user-1",
                schema_path=SCHEMA_PATH,
                store=store,
            )
            self.assertEqual(public_response.status_code, 201)
            self.assertEqual(store.list_public_results(), [])

            store.approve_public_submission(public_package["run_id"])
            public_results = store.list_public_results()

            self.assertEqual(len(public_results), 1)
            self.assertEqual(public_results[0]["run_id"], public_package["run_id"])
            self.assert_public_summary_shape(public_results[0])

    def test_rejected_public_submission_is_hidden(self) -> None:
        package = load_fixture("valid_private_upload.json")
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")

            response = ingest_result_request(
                {"result_package": package, "visibility": "submit_for_public_review"},
                user_id="user-1",
                schema_path=SCHEMA_PATH,
                store=store,
            )
            self.assertEqual(response.status_code, 201)

            store.reject_public_submission(package["run_id"])

            self.assertEqual(store.list_public_results(), [])
            self.assertIsNone(store.get_public_result(package["run_id"]))

    def test_public_detail_returns_approved_result_by_result_id_or_run_id_only(self) -> None:
        package = load_fixture("valid_private_upload.json")
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")

            response = ingest_result_request(
                {"result_package": package, "visibility": "submit_for_public_review"},
                user_id="user-1",
                schema_path=SCHEMA_PATH,
                store=store,
            )
            self.assertEqual(response.status_code, 201)
            self.assertIsNone(store.get_public_result(package["run_id"]))

            store.approve_public_submission(package["run_id"])
            by_run_id = store.get_public_result(package["run_id"])
            self.assertIsNotNone(by_run_id)
            by_result_id = store.get_public_result(by_run_id["result_id"])

            self.assertEqual(by_result_id, by_run_id)
            self.assert_public_summary_shape(by_run_id)

    def assert_public_summary_shape(self, summary: dict) -> None:
        required_fields = {
            "result_id",
            "run_id",
            "model_name",
            "model_revision",
            "quantization",
            "runtime_engine",
            "runtime_version",
            "hardware_label",
            "gpu",
            "gpu_count",
            "operating_system",
            "monitor_backend",
            "tci_v0_1",
            "factual_correctness_rate",
            "factual_incorrect_answer_rate",
            "factual_abstention_rate",
            "factual_attempted_accuracy",
            "local_ipw_unscaled",
            "local_ipw_displayed",
            "local_ipw_status",
            "gpu_energy_wh",
            "energy_confidence",
            "energy_warning_codes",
            "verification_level",
            "methodology_version",
            "evaluation_suite",
            "completed_tasks",
            "total_tasks",
            "completion_ratio",
            "error_count",
            "result_timestamp",
            "published_at",
        }
        self.assertTrue(required_fields.issubset(summary.keys()))
        serialized = json.dumps(summary).lower()
        for forbidden in [
            "raw_results",
            "raw_result_packages",
            "storage_path",
            "user_id",
            "submitted_by",
            "prompt",
            "response",
            "filename",
            "hostname",
            "serial_number",
            "api_key",
            "token",
            "password",
            "secret",
        ]:
            self.assertNotIn(forbidden, serialized)


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
