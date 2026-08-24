from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "apps" / "observatory-web"
FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "observatory" / "public_rows.json"

REQUIRED_RESULT_FIELDS = {
    "result_id",
    "run_id",
    "model_name",
    "hardware_label",
    "tci_v0_1",
    "factual_correctness_rate",
    "local_ipw_displayed",
    "local_ipw_status",
    "energy_confidence",
    "verification_level",
    "methodology_version",
}


class ObservatoryWebShellTests(unittest.TestCase):
    def test_static_shell_files_exist(self) -> None:
        for filename in ["index.html", "styles.css", "app.js", "public-results.js", "README.md"]:
            self.assertTrue((WEB_ROOT / filename).exists(), filename)

    def test_index_includes_logo_navigation_sections_and_scripts(self) -> None:
        html = (WEB_ROOT / "index.html").read_text()

        for expected in [
            "../../assets/telperia-logo.png",
            "A measurement layer for AI systems.",
            "Benchmark specimen",
            "Every measurement has provenance.",
            "The machine is part of the result.",
            "Explore Observatory",
            "Run Evaluation Runner",
            "Request Report",
            'id="home"',
            'id="observatory"',
            'id="methodology"',
            'id="benchmarks"',
            'id="research"',
            'id="about"',
            'id="status"',
            'id="result-detail"',
            "public-results.js",
            "app.js",
        ]:
            self.assertIn(expected, html)

    def test_public_results_data_matches_observatory_fixture_shape(self) -> None:
        fixture_rows = json.loads(FIXTURE_PATH.read_text())
        web_rows = load_public_results()

        self.assertEqual(web_rows, fixture_rows)
        for row in web_rows:
            self.assertTrue(REQUIRED_RESULT_FIELDS.issubset(row))
            self.assertNotIn("prompt", row)
            self.assertNotIn("response", row)

    def test_app_renders_expected_observatory_fields(self) -> None:
        script = (WEB_ROOT / "app.js").read_text()

        for expected in [
            "data-hero",
            "model_name",
            "hardware_label",
            "tci_v0_1",
            "factual_correctness_rate",
            "local_ipw_displayed",
            "energy_confidence",
            "verification_level",
            "methodology_version",
        ]:
            self.assertIn(expected, script)

        self.assertNotIn("innerHTML", script)

    def test_visual_system_avoids_ai_startup_cliches(self) -> None:
        css = (WEB_ROOT / "styles.css").read_text().lower()
        html = (WEB_ROOT / "index.html").read_text().lower()

        for forbidden in ["glassmorphism", "glowing", "blob", "particle", "robot", "brain"]:
            pattern = rf"\b{forbidden}\b"
            self.assertIsNone(re.search(pattern, html))
            self.assertIsNone(re.search(pattern, css))
        self.assertNotIn("linear-gradient", css)


def load_public_results() -> list[dict]:
    text = (WEB_ROOT / "public-results.js").read_text()
    match = re.fullmatch(r"window\.TELPERIA_PUBLIC_RESULTS = (.*);\n?", text, re.DOTALL)
    if match is None:
        raise AssertionError("public-results.js must assign window.TELPERIA_PUBLIC_RESULTS")
    return json.loads(match.group(1))


if __name__ == "__main__":
    unittest.main()
