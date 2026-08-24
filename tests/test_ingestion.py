from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_ROOT.parent
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
sys.path.insert(0, str(TESTS_ROOT))
sys.path.insert(0, str(RUNNER_ROOT))

from telperia_runner.ingestion import extract_observatory_row, validate_ingestion_package
from test_runner import make_package


SCHEMA_PATH = PROJECT_ROOT / "schemas" / "evaluation-run.schema.json"


class IngestionValidatorTests(unittest.TestCase):
    def test_accepts_valid_package_and_extracts_observatory_row(self) -> None:
        package = make_valid_energy_package()

        validation = validate_ingestion_package(package, SCHEMA_PATH)
        row = extract_observatory_row(
            package,
            result_id="public-result-1",
            published_at="2026-08-23T00:00:00Z",
        )

        self.assertTrue(validation.accepted)
        self.assertIsNone(validation.error_code)
        self.assertIn("verification_level_zero", validation.validation_warnings)
        self.assertEqual(row["result_id"], "public-result-1")
        self.assertEqual(row["model_name"], "llama3.1:8b")
        self.assertEqual(row["local_ipw_status"], "calculated")
        self.assertEqual(row["energy_confidence"], "low")
        self.assertEqual(row["verification_level"], 0)

    def test_rejects_private_prompt_or_response_fields(self) -> None:
        package = make_valid_energy_package()
        package["evaluation"]["scores"]["private_probe"] = {"prompt": "do not store me"}

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "privacy_violation")

    def test_rejects_private_content_aliases_and_sensitive_values(self) -> None:
        package = make_valid_energy_package()
        package["evaluation"]["scores"]["private_probe"] = {"promptText": "do not store me"}

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "privacy_violation")

    def test_rejects_sensitive_text_in_public_summary_fields(self) -> None:
        package = make_valid_energy_package()
        package["model"]["name"] = "response: private answer"

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "privacy_violation")

    def test_rejects_deeply_nested_privacy_payloads_without_crashing(self) -> None:
        package = make_valid_energy_package()
        nested = {}
        current = nested
        for _ in range(150):
            current["next"] = {}
            current = current["next"]
        package["evaluation"]["scores"]["nested_probe"] = nested

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "privacy_violation")

    def test_rejects_invalid_ipw_math(self) -> None:
        package = make_valid_energy_package()
        package["evaluation"]["scores"]["ipw_v0_1"]["unscaled"] = 999.0

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "energy_consistency_error")

    def test_accepts_missing_energy_confidence_with_warning(self) -> None:
        package = make_valid_energy_package()
        del package["energy"]["energy_confidence"]

        validation = validate_ingestion_package(package, SCHEMA_PATH)
        row = extract_observatory_row(package)

        self.assertTrue(validation.accepted)
        self.assertIn("energy_confidence_missing", validation.validation_warnings)
        self.assertIsNone(row["energy_confidence"])

    def test_rejects_inconsistent_completion_ratio(self) -> None:
        package = make_valid_energy_package()
        package["evaluation"]["completion_ratio"] = 0.5

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "metric_consistency_error")

    def test_rejects_forged_tci_category_score(self) -> None:
        package = make_valid_energy_package()
        package["evaluation"]["scores"]["tci_v0_1"]["categories"]["reasoning"]["category_score"] = 50.0

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "metric_consistency_error")

    def test_rejects_raw_result_score_outside_range(self) -> None:
        package = make_valid_energy_package()
        package["evaluation"]["raw_results"][0]["score"] = 42.0

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "metric_consistency_error")

    def test_rejects_missing_ingestion_fields(self) -> None:
        package = make_valid_energy_package()
        del package["run_environment"]

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "invalid_schema")

    def test_rejects_invalid_run_id_format(self) -> None:
        package = make_valid_energy_package()
        package["run_id"] = "not-a-uuid"

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "invalid_schema")

    def test_rejects_energy_summary_that_disagrees_with_raw_samples(self) -> None:
        package = make_valid_energy_package()
        package["energy"]["average_power_w"] = 500.0

        validation = validate_ingestion_package(package, SCHEMA_PATH)

        self.assertFalse(validation.accepted)
        self.assertEqual(validation.error_code, "energy_consistency_error")

    def test_does_not_treat_token_count_fields_as_private_content(self) -> None:
        package = make_valid_energy_package()
        token_package = copy.deepcopy(package)
        token_package["performance"]["input_tokens"] = 12
        token_package["performance"]["output_tokens"] = 18

        validation = validate_ingestion_package(token_package, SCHEMA_PATH)

        self.assertTrue(validation.accepted)


def make_valid_energy_package() -> dict:
    package = make_package(energy_wh=2.0)
    samples = [
        {"timestamp": "2026-08-23T00:00:00Z", "power_w": 100.0, "interval_s": 36.0},
        {"timestamp": "2026-08-23T00:00:36Z", "power_w": 100.0, "interval_s": 36.0},
    ]
    package["energy"]["raw_power_samples"] = samples
    package["energy"]["average_power_w"] = 100.0
    package["energy"]["peak_power_w"] = 100.0
    package["energy"]["energy_confidence"] = {
        "quality": "low",
        "sample_count": len(samples),
        "measured_duration_s": 72.0,
        "minimum_recommended_samples": 10,
        "minimum_recommended_duration_s": 30.0,
        "warning_codes": ["low_sample_count", "gross_energy_scope"],
    }
    return package


if __name__ == "__main__":
    unittest.main()
