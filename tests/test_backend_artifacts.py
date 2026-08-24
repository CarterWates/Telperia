from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
sys.path.insert(0, str(RUNNER_ROOT))

from telperia_runner.ingestion import extract_observatory_row, validate_ingestion_package


SCHEMA_PATH = PROJECT_ROOT / "schemas" / "evaluation-run.schema.json"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "ingestion"
MIGRATION_PATH = PROJECT_ROOT / "supabase" / "migrations" / "20260823000000_phase_6_result_ingestion.sql"
API_CONTRACT_PATH = PROJECT_ROOT / "docs" / "result-ingestion-api.md"
API_README_PATH = PROJECT_ROOT / "apps" / "api" / "README.md"
WINDOWS_RUNBOOK_PATH = PROJECT_ROOT / "docs" / "windows-test-contributor-runbook.md"
DOCS_README_PATH = PROJECT_ROOT / "docs" / "README.md"
SECURITY_PATH = PROJECT_ROOT / "SECURITY.md"
OBSERVATORY_FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "observatory" / "public_rows.json"
OBSERVATORY_README_PATH = PROJECT_ROOT / "tests" / "fixtures" / "observatory" / "README.md"

OBSERVATORY_REQUIRED_FIELDS = {
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
OBSERVATORY_PRIVATE_FIELDS = {
    "user_id",
    "email",
    "storage_path",
    "prompt",
    "response",
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
}


class SupabaseMigrationDraftTests(unittest.TestCase):
    def test_phase_6_migration_defines_core_tables_indexes_rls_and_storage(self) -> None:
        sql = MIGRATION_PATH.read_text()

        for table_name in [
            "profiles",
            "result_uploads",
            "model_configs",
            "hardware_profiles",
            "evaluation_runs",
            "run_scores",
            "public_submissions",
        ]:
            self.assertIn(f"create table if not exists public.{table_name}", sql)
            self.assertIn(f"alter table public.{table_name} enable row level security", sql)

        for expected in [
            "create type public.result_visibility",
            "create type public.ingestion_status",
            "create type public.public_submission_status",
            "create type public.local_ipw_status",
            "create index if not exists result_uploads_user_id_idx",
            "create index if not exists evaluation_runs_public_lookup_idx",
            "create index if not exists run_scores_tci_v0_1_idx",
            "insert into storage.buckets",
            "create policy \"Users can read their own result package objects\"",
            "comment on table public.result_uploads",
            "revoke all on table public.result_uploads from anon, authenticated",
            "alter table storage.objects enable row level security",
        ]:
            self.assertIn(expected, sql)

        self.assertNotIn("service" + "_role", sql)
        self.assertNotIn("security definer", sql.lower())
        self.assertNotIn("grant select on table public.evaluation_runs to anon", sql)
        self.assertNotIn("grant select on table public.run_scores to anon", sql)
        self.assertNotIn("to anon, authenticated", sql)
        self.assertNotIn("Anyone can read public runs", sql)
        self.assertNotIn("Anyone can read scores for public runs", sql)
        self.assertNotIn("on storage.objects for insert\nto authenticated", sql)
        self.assertNotIn("on public.result_uploads for insert\nto authenticated", sql)
        self.assertNotIn("on public.evaluation_runs for insert\nto authenticated", sql)
        self.assertNotIn("on public.run_scores for insert\nto authenticated", sql)
        self.assertNotIn("on public.public_submissions for insert\nto authenticated", sql)


class ResultIngestionApiContractTests(unittest.TestCase):
    def test_api_contract_defines_endpoint_errors_and_parseable_json_examples(self) -> None:
        document = API_CONTRACT_PATH.read_text()

        for expected in [
            "POST /api/results/ingest",
            "Authorization: Bearer",
            "private",
            "submit_for_public_review",
            "invalid_schema",
            "privacy_violation",
            "energy_consistency_error",
            "duplicate_run_id",
            "evaluation-runner/telperia_runner/ingestion.py",
        ]:
            self.assertIn(expected, document)

        examples = extract_json_blocks(document)
        self.assertGreaterEqual(len(examples), 4)
        for example in examples:
            json.loads(example)


class ApiServiceDesignTests(unittest.TestCase):
    def test_api_readme_connects_validator_migration_storage_and_review_flow(self) -> None:
        document = API_README_PATH.read_text()

        for expected in [
            "Phase 6 API Service",
            "evaluation-runner/telperia_runner/ingestion.py",
            "supabase/migrations/20260823000000_phase_6_result_ingestion.sql",
            "result-packages",
            "public_submissions",
            "docs/result-ingestion-api.md",
            "private",
            "submit_for_public_review",
            "no prompt or response content",
        ]:
            self.assertIn(expected, document)


class WindowsContributorRunbookTests(unittest.TestCase):
    def test_windows_runbook_covers_clean_model_testing_workflow(self) -> None:
        document = WINDOWS_RUNBOOK_PATH.read_text()

        for expected in [
            "Windows Test Contributor Runbook",
            "git clone",
            "python -m unittest discover -s tests -q",
            "ollama pull",
            "python evaluation-runner/evaluate.py",
            "--hardware-monitor nvml",
            "--node-id windows-5070",
            "git checkout -b",
            "git push",
            "Do not commit prompt text or response text",
        ]:
            self.assertIn(expected, document)


class DocumentationNavigationTests(unittest.TestCase):
    def test_docs_readme_explains_reading_paths(self) -> None:
        document = DOCS_README_PATH.read_text()

        for expected in [
            "Read These Docs In This Order",
            "Contributors",
            "Methodology Readers",
            "Backend Work",
            "Local Testing",
            "docs/roadmap.md",
            "docs/telperia-methodology-v0.1.md",
            "docs/result-ingestion-api.md",
            "docs/windows-test-contributor-runbook.md",
        ]:
            self.assertIn(expected, document)


class SecurityChecklistTests(unittest.TestCase):
    def test_security_checklist_covers_telperia_risks(self) -> None:
        document = SECURITY_PATH.read_text()

        for expected in [
            "Telperia Security Review Checklist",
            "Secrets",
            "Prompt And Response Privacy",
            "Public Uploads",
            "RLS",
            "Private Raw JSON",
            "Dataset Review",
            "Release Checklist",
            "result-packages",
            "Supabase Security Advisor",
            "Do not commit",
        ]:
            self.assertIn(expected, document)


class ObservatoryFixtureTests(unittest.TestCase):
    def test_public_rows_fixture_matches_public_data_shape(self) -> None:
        rows = json.loads(OBSERVATORY_FIXTURE_PATH.read_text())

        self.assertGreaterEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(set(row), OBSERVATORY_REQUIRED_FIELDS)
            self.assertTrue(OBSERVATORY_PRIVATE_FIELDS.isdisjoint(row))
            self.assertIn(row["local_ipw_status"], ["calculated", "deferred"])
            self.assertIn(row["energy_confidence"], ["unavailable", "low", "medium", "high", None])
            self.assertEqual(row["methodology_version"], "0.1")
            self.assertEqual(row["evaluation_suite"], "tci-v0.1")
            self.assertGreaterEqual(row["tci_v0_1"], 0)
            self.assertLessEqual(row["tci_v0_1"], 100)
            self.assertGreaterEqual(row["completion_ratio"], 0)
            self.assertLessEqual(row["completion_ratio"], 1)

    def test_public_rows_fixture_matches_extracted_ingestion_summaries(self) -> None:
        rows = json.loads(OBSERVATORY_FIXTURE_PATH.read_text())
        packages = [
            load_fixture("valid_private_upload.json"),
            load_fixture("low_energy_confidence_warning.json"),
            load_fixture("duplicate_run_id_original.json"),
        ]
        expected = [
            extract_observatory_row(package, result_id=f"public-fixture-{index}", published_at="2026-08-23T00:00:00Z")
            for index, package in enumerate(packages, start=1)
        ]

        self.assertEqual(rows, expected)

    def test_observatory_fixture_readme_links_data_shape_contract(self) -> None:
        readme = OBSERVATORY_README_PATH.read_text()

        self.assertIn("docs/observatory-data-shape.md", readme)
        self.assertIn("public_rows.json", readme)


class IngestionFixtureTests(unittest.TestCase):
    def test_fixture_valid_private_upload_is_accepted(self) -> None:
        package = load_fixture("valid_private_upload.json")

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertTrue(validation.accepted)
        self.assertEqual(validation.validation_warnings, ["low_energy_confidence", "verification_level_zero"])

    def test_fixture_rejected_prompt_response_content_is_rejected(self) -> None:
        package = load_fixture("rejected_prompt_response_content.json")

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "privacy_violation")

    def test_fixture_invalid_ipw_math_is_rejected(self) -> None:
        package = load_fixture("invalid_ipw_math.json")

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "energy_consistency_error")

    def test_fixture_duplicate_run_id_pair_shares_run_id_with_different_content(self) -> None:
        first = load_fixture("duplicate_run_id_original.json")
        second = load_fixture("duplicate_run_id_changed.json")

        self.assertEqual(first["run_id"], second["run_id"])
        self.assertNotEqual(first, second)
        self.assertTrue(validate_ingestion_package(first, SCHEMA_PATH).accepted)
        self.assertTrue(validate_ingestion_package(second, SCHEMA_PATH).accepted)

    def test_fixture_low_energy_confidence_is_accepted_with_warning(self) -> None:
        package = load_fixture("low_energy_confidence_warning.json")

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertTrue(validation.accepted)
        self.assertIn("low_energy_confidence", validation.validation_warnings)


def load_fixture(filename: str) -> dict:
    return json.loads((FIXTURE_ROOT / filename).read_text())


def extract_json_blocks(document: str) -> list[str]:
    blocks = []
    inside_json = False
    current: list[str] = []
    for line in document.splitlines():
        if line == "```json":
            inside_json = True
            current = []
            continue
        if line == "```" and inside_json:
            inside_json = False
            blocks.append("\n".join(current))
            continue
        if inside_json:
            current.append(line)
    return blocks


if __name__ == "__main__":
    unittest.main()
