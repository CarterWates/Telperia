from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
API_ROOT = PROJECT_ROOT / "apps" / "api"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "ingestion"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "evaluation-run.schema.json"

sys.path.insert(0, str(RUNNER_ROOT))
sys.path.insert(0, str(API_ROOT))

from telperia_api.http_app import LocalApiConfig, handle_local_request
from telperia_api.ingestion_service import InMemoryIngestionStore
from telperia_api.persistence import SQLiteIngestionStore


class LocalHttpApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = LocalApiConfig(schema_path=SCHEMA_PATH, store=InMemoryIngestionStore())

    def test_health_endpoint_reports_local_backend_status(self) -> None:
        response = handle_local_request("GET", "/health", {}, b"", self.config)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.payload["status"], "ok")
        self.assertEqual(response.payload["service"], "telperia-api")
        self.assertEqual(response.payload["mode"], "local")
        self.assertEqual(response.payload["supabase"], "disabled")

    def test_ingest_endpoint_accepts_valid_private_upload_without_real_auth(self) -> None:
        body = {"result_package": load_fixture("valid_private_upload.json")}

        response = handle_local_request("POST", "/api/results/ingest", {}, encode_json(body), self.config)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.payload["ingestion_status"], "accepted")
        self.assertEqual(response.payload["visibility"], "private")
        self.assertEqual(response.payload["run_id"], body["result_package"]["run_id"])

    def test_ingest_endpoint_rejects_invalid_schema(self) -> None:
        package = load_fixture("valid_private_upload.json")
        del package["model"]

        response = handle_local_request(
            "POST",
            "/api/results/ingest",
            {},
            encode_json({"result_package": package}),
            self.config,
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.payload["ingestion_status"], "rejected")
        self.assertEqual(response.payload["error_code"], "invalid_schema")

    def test_ingest_endpoint_rejects_privacy_content(self) -> None:
        body = {"result_package": load_fixture("rejected_prompt_response_content.json")}

        response = handle_local_request("POST", "/api/results/ingest", {}, encode_json(body), self.config)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.payload["error_code"], "privacy_violation")

    def test_ingest_endpoint_rejects_direct_public_visibility(self) -> None:
        body = {"result_package": load_fixture("valid_private_upload.json"), "visibility": "public"}

        response = handle_local_request("POST", "/api/results/ingest", {}, encode_json(body), self.config)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.payload["error_code"], "invalid_visibility")

    def test_ingest_endpoint_accepts_public_review_request(self) -> None:
        body = {
            "result_package": load_fixture("valid_private_upload.json"),
            "visibility": "submit_for_public_review",
        }

        response = handle_local_request(
            "POST",
            "/api/results/ingest",
            {"x-telperia-user-id": "local-reviewer"},
            encode_json(body),
            self.config,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.payload["visibility"], "submitted_for_public_review")
        self.assertEqual(response.payload["public_submission_status"], "pending_review")

    def test_ingest_endpoint_can_use_sqlite_persistence(self) -> None:
        body = {"result_package": load_fixture("valid_private_upload.json")}
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")
            config = LocalApiConfig(schema_path=SCHEMA_PATH, store=store, storage_mode="sqlite")

            response = handle_local_request("POST", "/api/results/ingest", {}, encode_json(body), config)
            health = handle_local_request("GET", "/health", {}, b"", config)

            self.assertEqual(response.status_code, 201)
            self.assertEqual(health.payload["storage"], "sqlite")
            self.assertEqual(store.table_count("result_uploads"), 1)

    def test_public_results_endpoint_returns_only_approved_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")
            config = LocalApiConfig(schema_path=SCHEMA_PATH, store=store, storage_mode="sqlite")
            pending_package = load_fixture("valid_private_upload.json")
            approved_package = load_fixture("duplicate_run_id_changed.json")

            pending = handle_local_request(
                "POST",
                "/api/results/ingest",
                {},
                encode_json({"result_package": pending_package, "visibility": "submit_for_public_review"}),
                config,
            )
            approved = handle_local_request(
                "POST",
                "/api/results/ingest",
                {},
                encode_json({"result_package": approved_package, "visibility": "submit_for_public_review"}),
                config,
            )
            self.assertEqual(pending.status_code, 201)
            self.assertEqual(approved.status_code, 201)

            store.approve_public_submission(approved_package["run_id"])
            response = handle_local_request("GET", "/api/public/results", {}, b"", config)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.payload["results"]), 1)
            self.assertEqual(response.payload["results"][0]["run_id"], approved_package["run_id"])
            self.assertEqual(response.payload["count"], 1)
            serialized = json.dumps(response.payload).lower()
            self.assertNotIn("raw_results", serialized)
            self.assertNotIn("storage_path", serialized)
            self.assertNotIn("user_id", serialized)
            self.assertNotIn("prompt", serialized)
            self.assertNotIn("response", serialized)

    def test_public_result_detail_endpoint_returns_approved_result_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteIngestionStore(Path(directory) / "telperia.db")
            config = LocalApiConfig(schema_path=SCHEMA_PATH, store=store, storage_mode="sqlite")
            package = load_fixture("valid_private_upload.json")

            upload = handle_local_request(
                "POST",
                "/api/results/ingest",
                {},
                encode_json({"result_package": package, "visibility": "submit_for_public_review"}),
                config,
            )
            self.assertEqual(upload.status_code, 201)

            hidden = handle_local_request("GET", f"/api/public/results/{package['run_id']}", {}, b"", config)
            self.assertEqual(hidden.status_code, 404)

            store.approve_public_submission(package["run_id"])
            visible = handle_local_request("GET", f"/api/public/results/{package['run_id']}", {}, b"", config)

            self.assertEqual(visible.status_code, 200)
            self.assertEqual(visible.payload["result"]["run_id"], package["run_id"])
            self.assertIn("methodology_version", visible.payload["result"])

    def test_ingest_endpoint_rejects_malformed_json(self) -> None:
        response = handle_local_request("POST", "/api/results/ingest", {}, b"{", self.config)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.payload["error_code"], "invalid_request_body")


def encode_json(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")


def load_fixture(filename: str) -> dict:
    return json.loads((FIXTURE_ROOT / filename).read_text())


if __name__ == "__main__":
    unittest.main()
