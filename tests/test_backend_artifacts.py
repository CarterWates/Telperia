from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
sys.path.insert(0, str(RUNNER_ROOT))

from telperia_runner.ingestion import validate_ingestion_package


SCHEMA_PATH = PROJECT_ROOT / "schemas" / "evaluation-run.schema.json"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "ingestion"
MIGRATION_PATH = PROJECT_ROOT / "supabase" / "migrations" / "20260823000000_phase_6_result_ingestion.sql"


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
        ]:
            self.assertIn(expected, sql)

        self.assertNotIn("service" + "_role", sql)
        self.assertNotIn("security definer", sql.lower())


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


if __name__ == "__main__":
    unittest.main()
