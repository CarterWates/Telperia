from __future__ import annotations

import json
import re
import struct
import unittest
import zlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "apps" / "observatory-web"
FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "observatory" / "public_rows.json"
PROFILE_FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "observatory" / "model_profiles.json"

REQUIRED_RESULT_FIELDS = {
    "result_id",
    "run_id",
    "model_name",
    "model_revision",
    "hardware_label",
    "tci_v0_1",
    "factual_correctness_rate",
    "factual_incorrect_answer_rate",
    "factual_abstention_rate",
    "factual_attempted_accuracy",
    "local_ipw_displayed",
    "local_ipw_status",
    "energy_confidence",
    "verification_level",
    "methodology_version",
    "evaluation_suite",
    "completion_ratio",
}


class ObservatoryWebShellTests(unittest.TestCase):
    def test_static_shell_files_exist(self) -> None:
        for filename in [
            "index.html",
            "styles.css",
            "app.js",
            "public-results.js",
            "public-model-profiles.js",
            "README.md",
            "assets/telperia-logo.png",
        ]:
            self.assertTrue((WEB_ROOT / filename).exists(), filename)

    def test_index_includes_logo_navigation_sections_and_scripts(self) -> None:
        html = (WEB_ROOT / "index.html").read_text()

        for expected in [
            "assets/telperia-logo.png",
            "A measurement layer for AI systems.",
            "Capability alone is not enough context.",
            "TRI: Not yet scored",
            "Transparency Evidence",
            "Local-first contribution",
            "private by default",
            "approved public summaries",
            "Benchmark specimen",
            "Every measurement has provenance.",
            "The machine is part of the result.",
            "Explore Observatory",
            "Run Evaluation Runner",
            "Request Report",
            'id="home"',
            'id="observatory"',
            'id="models"',
            'id="model-profile"',
            'id="methodology"',
            'id="benchmarks"',
            'id="research"',
            'id="about"',
            'id="status"',
            'id="result-detail"',
            "public-results.js",
            "public-model-profiles.js",
            "app.js",
        ]:
            self.assertIn(expected, html)

    def test_index_includes_public_model_directory_without_numeric_transparency_score(self) -> None:
        html = (WEB_ROOT / "index.html").read_text()
        lower_html = html.lower()

        for expected in [
            "Public Model Directory",
            "data-summary=\"model-count\"",
            "id=\"model-directory\"",
            "id=\"model-summary\"",
            "View profile",
            "Provider",
            "Open status",
            "Transparency Evidence",
            "Available Local IPW",
        ]:
            self.assertIn(expected, html)

        for forbidden in [
            "transparency score",
            "tri score",
            "universal winner",
            "overall winner",
        ]:
            self.assertNotIn(forbidden, lower_html)

    def test_index_includes_public_model_profile_view_without_deferred_scores(self) -> None:
        html = (WEB_ROOT / "index.html").read_text()
        lower_html = html.lower()

        for expected in [
            "Model Profile",
            "id=\"profile-title\"",
            "id=\"profile-summary\"",
            "id=\"profile-tci-breakdown\"",
            "id=\"profile-factual-breakdown\"",
            "id=\"profile-ipw-runs\"",
            "id=\"profile-limitations\"",
            "id=\"profile-download\"",
            "TCI Breakdown",
            "Factual Reliability Breakdown",
            "TRI: Not yet scored",
            "Transparency Evidence",
            "Hardware-specific Local IPW",
            "Latency",
            "Throughput",
            "Energy",
            "Verification Level",
            "Methodology Version",
            "Limitations",
            "Result package download",
        ]:
            self.assertIn(expected, html)

        for forbidden in [
            "transparency score",
            "tri score",
        ]:
            self.assertNotIn(forbidden, lower_html)

    def test_index_positions_telperia_as_energy_aware_without_overclaiming(self) -> None:
        html = (WEB_ROOT / "index.html").read_text()
        lower_html = html.lower()

        for expected in [
            "energy-aware AI measurement",
            "what intelligence costs to run",
            "capability per watt-hour",
            "hardware-specific efficiency",
            "local inference energy",
        ]:
            self.assertIn(expected, html)

        for forbidden in [
            "carbon neutral",
            "carbon footprint",
            "data-center energy measurement",
            "datacenter energy measurement",
            "full data-center energy",
            "full datacenter energy",
        ]:
            self.assertNotIn(forbidden, lower_html)

    def test_public_results_data_matches_observatory_fixture_shape(self) -> None:
        fixture_rows = json.loads(FIXTURE_PATH.read_text())
        web_rows = load_public_results()

        self.assertEqual(web_rows, fixture_rows)
        self.assertGreaterEqual(len(web_rows), 10)
        self.assertGreaterEqual(len({row["model_name"] for row in web_rows}), 5)
        for row in web_rows:
            self.assertTrue(REQUIRED_RESULT_FIELDS.issubset(row))
            self.assertNotIn("prompt", row)
            self.assertNotIn("response", row)
            self.assertGreaterEqual(row["factual_correctness_rate"], 0)
            self.assertLessEqual(row["factual_correctness_rate"], 1)
            self.assertGreaterEqual(row["factual_incorrect_answer_rate"], 0)
            self.assertLessEqual(row["factual_incorrect_answer_rate"], 1)
            self.assertGreaterEqual(row["factual_abstention_rate"], 0)
            self.assertLessEqual(row["factual_abstention_rate"], 1)
            self.assertGreaterEqual(row["factual_attempted_accuracy"], 0)
            self.assertLessEqual(row["factual_attempted_accuracy"], 1)
            self.assertEqual(row["verification_level"], 0)

    def test_public_model_profile_data_matches_fixture_and_stays_public_safe(self) -> None:
        fixture_profiles = json.loads(PROFILE_FIXTURE_PATH.read_text())
        web_profiles = load_public_model_profiles()

        self.assertEqual(web_profiles, fixture_profiles)
        self.assertGreaterEqual(len(web_profiles), 5)

        rows = load_public_results()
        self.assertEqual(
            sorted(profile["model_name"] for profile in web_profiles),
            sorted({row["model_name"] for row in rows}),
        )

        for profile in web_profiles:
            self.assertEqual(profile["provider"], "unknown")
            self.assertEqual(profile["open_status"], "unknown")
            self.assertGreaterEqual(profile["run_count"], 1)
            self.assertTrue(profile["tci_breakdown"])
            self.assertTrue(profile["hardware_specific_ipw_runs"])
            self.assertEqual(profile["tri"]["status"], "not_yet_scored")
            self.assertEqual(profile["download"]["status"], "placeholder")
            self.assertIn("not yet scored", profile["tri"]["label"].lower())
            self.assertIn("result package download", profile["download"]["label"].lower())
            self.assertTrue(profile["limitations"])
            self.assert_public_safe(profile)

    def test_app_renders_expected_observatory_fields(self) -> None:
        script = (WEB_ROOT / "app.js").read_text()

        for expected in [
            "data-hero",
            "model_name",
            "hardware_label",
            "tci_v0_1",
            "factual_correctness_rate",
            "factual_incorrect_answer_rate",
            "factual_abstention_rate",
            "factual_attempted_accuracy",
            "local_ipw_unscaled",
            "local_ipw_displayed",
            "energy_confidence",
            "verification_level",
            "methodology_version",
            "Level 0 means local/self-run evidence",
            "formatIpwDisplayScore",
            "IPW Display Score",
            "chooseHeroResult",
        ]:
            self.assertIn(expected, script)

        self.assertNotIn("innerHTML", script)

    def test_app_renders_public_model_profiles(self) -> None:
        script = (WEB_ROOT / "app.js").read_text()

        for expected in [
            "TELPERIA_MODEL_PROFILES",
            "renderModelProfile",
            "modelProfiles",
            "profileTitle",
            "profileSummary",
            "profileTciBreakdown",
            "profileFactualBreakdown",
            "profileIpwRuns",
            "profileLimitations",
            "profileDownload",
            "TRI: Not yet scored",
            "Transparency Evidence",
            "Latency",
            "Throughput",
            "Energy",
            "Verification Level",
            "Methodology Version",
            "profile.download.label",
            "formatLatency",
            "formatThroughput",
        ]:
            self.assertIn(expected, script)

        for forbidden in [
            "transparency_score",
            "tri_score",
            "owner",
            "storage_path",
            ".prompt",
            ".response",
        ]:
            self.assertNotIn(forbidden, script)

    def test_primary_ipw_display_uses_unscaled_value_with_units(self) -> None:
        html = (WEB_ROOT / "index.html").read_text()
        script = (WEB_ROOT / "app.js").read_text()

        self.assertIn('data-hero="local_ipw_unscaled"', html)
        self.assertIn("local_ipw_unscaled", script)
        self.assertIn('return `${formatNumber(row.local_ipw_unscaled)} TCI/Wh`;', script)
        self.assertIn('["IPW Display Score", formatIpwDisplayScore(row)]', script)
        self.assertNotIn('key === "local_ipw_displayed"', script)

    def test_homepage_hero_selects_richer_seed_result(self) -> None:
        script = (WEB_ROOT / "app.js").read_text()

        self.assertIn("const heroResult = chooseHeroResult(results);", script)
        self.assertIn("row.local_ipw_status === \"calculated\"", script)
        self.assertIn("row.factual_incorrect_answer_rate > 0", script)
        self.assertIn("row.gpu_energy_wh > 0", script)
        self.assertIn("updateHeroSpecimen(heroResult);", script)

    def test_app_groups_public_rows_into_model_directory(self) -> None:
        script = (WEB_ROOT / "app.js").read_text()
        rows = load_public_results()
        expected_model_count = len({row["model_name"] for row in rows})

        self.assertGreaterEqual(expected_model_count, 5)
        for expected in [
            "summarizeModels",
            "renderModelDirectory",
            "selectModel",
            "provider: \"unknown\"",
            "openStatus: \"unknown\"",
            "Transparency Evidence",
            "Available Local IPW",
            "No universal winner",
        ]:
            self.assertIn(expected, script)

        for forbidden in [
            "transparency_score",
            "tri_score",
            "owner",
            "storage_path",
            ".prompt",
            ".response",
        ]:
            self.assertNotIn(forbidden, script)

    def test_visual_system_avoids_ai_startup_cliches(self) -> None:
        css = (WEB_ROOT / "styles.css").read_text().lower()
        html = (WEB_ROOT / "index.html").read_text().lower()

        for forbidden in ["glassmorphism", "glowing", "blob", "particle", "robot", "brain"]:
            pattern = rf"\b{forbidden}\b"
            self.assertIsNone(re.search(pattern, html))
            self.assertIsNone(re.search(pattern, css))
        self.assertNotIn("linear-gradient", css)

    def test_hero_layout_uses_viewport_safe_desktop_scale(self) -> None:
        css = (WEB_ROOT / "styles.css").read_text()

        h1_match = re.search(r"h1\s*{[^}]*font-size:\s*([0-9.]+)rem;", css)
        self.assertIsNotNone(h1_match)
        self.assertLessEqual(float(h1_match.group(1)), 5.6)
        self.assertIn("grid-template-columns: minmax(0, 0.52fr) minmax(340px, 0.48fr);", css)
        self.assertIn("max-width: 620px;", css)
        self.assertIn("@media (max-width: 1180px)", css)

    def test_logo_asset_preserves_transparency(self) -> None:
        transparent, opaque = count_png_alpha_states(WEB_ROOT / "assets" / "telperia-logo.png")
        css = (WEB_ROOT / "styles.css").read_text()
        brand_image_rule = re.search(r"\.brand img\s*{[^}]*}", css)

        self.assertGreater(transparent, 0)
        self.assertGreater(opaque, 0)
        self.assertIsNotNone(brand_image_rule)
        self.assertNotIn("background", brand_image_rule.group(0))


def load_public_results() -> list[dict]:
    text = (WEB_ROOT / "public-results.js").read_text()
    match = re.fullmatch(r"window\.TELPERIA_PUBLIC_RESULTS = (.*);\n?", text, re.DOTALL)
    if match is None:
        raise AssertionError("public-results.js must assign window.TELPERIA_PUBLIC_RESULTS")
    return json.loads(match.group(1))


def load_public_model_profiles() -> list[dict]:
    text = (WEB_ROOT / "public-model-profiles.js").read_text()
    match = re.fullmatch(r"window\.TELPERIA_MODEL_PROFILES = (.*);\n?", text, re.DOTALL)
    if match is None:
        raise AssertionError("public-model-profiles.js must assign window.TELPERIA_MODEL_PROFILES")
    return json.loads(match.group(1))


def assert_no_public_private_fields(test_case: unittest.TestCase, value: object) -> None:
    forbidden_keys = {
        "prompt",
        "prompt_text",
        "response",
        "response_text",
        "filename",
        "file_path",
        "hostname",
        "serial_number",
        "owner",
        "user_id",
        "email",
        "storage_path",
        "api_key",
        "password",
        "secret",
    }

    def walk(item: object) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                test_case.assertNotIn(key.lower(), forbidden_keys)
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)


ObservatoryWebShellTests.assert_public_safe = assert_no_public_private_fields


def count_png_alpha_states(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError("logo asset must be a PNG")

    position = 8
    width = height = bit_depth = color_type = None
    idat_chunks = []
    while position < len(data):
        length = struct.unpack(">I", data[position : position + 4])[0]
        chunk_type = data[position + 4 : position + 8]
        chunk = data[position + 8 : position + 8 + length]
        position += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, *_ = struct.unpack(">IIBBBBB", chunk)
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk)
        elif chunk_type == b"IEND":
            break

    if bit_depth != 8 or color_type != 6:
        raise AssertionError("logo asset must be an 8-bit RGBA PNG")

    raw = zlib.decompress(b"".join(idat_chunks))
    bytes_per_pixel = 4
    stride = width * bytes_per_pixel
    previous = [0] * stride
    transparent = 0
    opaque = 0
    pointer = 0

    for _ in range(height):
        filter_type = raw[pointer]
        pointer += 1
        scanline = list(raw[pointer : pointer + stride])
        pointer += stride
        row = [0] * stride
        for index, value in enumerate(scanline):
            left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            up = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                paeth = left + up - upper_left
                left_distance = abs(paeth - left)
                up_distance = abs(paeth - up)
                corner_distance = abs(paeth - upper_left)
                predictor = (
                    left
                    if left_distance <= up_distance and left_distance <= corner_distance
                    else up
                    if up_distance <= corner_distance
                    else upper_left
                )
            else:
                raise AssertionError(f"unsupported PNG filter: {filter_type}")
            row[index] = (value + predictor) & 255
        alpha_values = row[3::4]
        transparent += sum(1 for alpha in alpha_values if alpha == 0)
        opaque += sum(1 for alpha in alpha_values if alpha > 0)
        previous = row

    return transparent, opaque


if __name__ == "__main__":
    unittest.main()
