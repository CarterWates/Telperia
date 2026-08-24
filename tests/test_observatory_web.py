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
        for filename in [
            "index.html",
            "styles.css",
            "app.js",
            "public-results.js",
            "README.md",
            "assets/telperia-logo.png",
        ]:
            self.assertTrue((WEB_ROOT / filename).exists(), filename)

    def test_index_includes_logo_navigation_sections_and_scripts(self) -> None:
        html = (WEB_ROOT / "index.html").read_text()

        for expected in [
            "assets/telperia-logo.png",
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
