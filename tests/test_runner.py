import json
import sys
import unittest
from contextlib import redirect_stderr
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_ROOT = PROJECT_ROOT / "evaluation-runner"
sys.path.insert(0, str(RUNNER_ROOT))

from telperia_runner.metrics import calculate_completion_ratio, calculate_factual_reliability, calculate_ipw, calculate_tci
from telperia_runner.monitor import NvmlBackgroundMonitor
from telperia_runner.ollama import OllamaClient
from telperia_runner.evaluator import run_evaluation, score_text
from telperia_runner.result import EvaluationResult, build_result_package
from telperia_runner.schema import SchemaValidationError, validate_result_package
from telperia_runner.suite import EvaluationTask, load_suite
from telperia_telemetry.models import GpuMetrics, TelemetrySample


class MetricsTests(unittest.TestCase):
    def test_calculates_completion_ratio(self) -> None:
        ratio = calculate_completion_ratio(completed_tasks=3, total_tasks=5)

        self.assertEqual(ratio, 0.6)

    def test_calculates_factual_reliability_rates(self) -> None:
        metrics = calculate_factual_reliability(correct=2, incorrect=1, abstentions=1)

        self.assertEqual(metrics["total_questions"], 4)
        self.assertEqual(metrics["correctness_rate"], 0.5)
        self.assertEqual(metrics["incorrect_answer_rate"], 0.25)
        self.assertEqual(metrics["abstention_rate"], 0.25)
        self.assertAlmostEqual(metrics["attempted_accuracy"], 2 / 3)

    def test_calculates_tci_with_raw_normalized_category_and_weights(self) -> None:
        results = [
            make_result(task_id="reasoning-001", category="reasoning", score=0.8),
            make_result(task_id="coding-001", category="coding", score=0.6),
            make_result(task_id="math-001", category="mathematics", score=0.5),
            make_result(task_id="factual-001", category="factual_knowledge", score=1.0),
            make_result(task_id="instruction-001", category="instruction_adherence", score=0.4),
        ]

        tci = calculate_tci(results)

        self.assertAlmostEqual(tci["final_score"], 66.0)
        reasoning = tci["categories"]["reasoning"]
        self.assertEqual(reasoning["category_weight"], 0.25)
        self.assertAlmostEqual(reasoning["category_score"], 80.0)
        self.assertEqual(reasoning["benchmarks"][0]["raw_benchmark_score"], 0.8)
        self.assertAlmostEqual(reasoning["benchmarks"][0]["normalized_benchmark_score"], 80.0)

    def test_calculates_ipw_when_energy_is_positive(self) -> None:
        ipw = calculate_ipw(tci=0.75, completion_ratio=0.8, gpu_energy_wh=0.5)

        self.assertAlmostEqual(ipw["unscaled"], 1.2)
        self.assertAlmostEqual(ipw["displayed"], 1200.0)

    def test_rejects_ipw_without_positive_energy(self) -> None:
        with self.assertRaises(ValueError):
            calculate_ipw(tci=0.75, completion_ratio=0.8, gpu_energy_wh=0.0)


class OllamaClientTests(unittest.TestCase):
    def test_generate_posts_prompt_and_records_token_counts(self) -> None:
        client = OllamaClient(base_url="http://ollama.test", opener=FakeOpener())

        result = client.generate(model="llama3.1:8b", prompt="Say hello.")

        self.assertTrue(result.success)
        self.assertEqual(result.output_tokens, 4)
        self.assertEqual(result.input_tokens, 3)
        self.assertGreaterEqual(result.latency_ms, 0)

    def test_version_supports_urllib_style_urlopen(self) -> None:
        client = OllamaClient(base_url="http://ollama.test", opener=FakeUrlopen())

        version = client.version()

        self.assertEqual(version, "0.1.0")

    def test_generate_marks_ollama_error_payload_as_failure(self) -> None:
        client = OllamaClient(base_url="http://ollama.test", opener=FakeErrorOpener())

        result = client.generate(model="missing-model", prompt="Say hello.")

        self.assertFalse(result.success)
        self.assertEqual(result.error_category, "ollama_error")
        self.assertEqual(result.output_tokens, 0)


class ScoringTests(unittest.TestCase):
    def test_exact_match_rejects_extra_text(self) -> None:
        task = EvaluationTask(
            task_id="instruction-001",
            category="instruction_adherence",
            prompt="Return only ABC-123.",
            expected_contains=["ABC-123"],
            exact_match=True,
        )

        self.assertEqual(score_text("ABC-123 extra", task), 0.0)
        self.assertEqual(score_text("ABC-123", task), 1.0)

    def test_case_sensitive_matching_is_optional(self) -> None:
        task = EvaluationTask(
            task_id="instruction-002",
            category="instruction_adherence",
            prompt="Return Go.",
            expected_contains=["Go"],
            case_sensitive=True,
        )

        self.assertEqual(score_text("go", task), 0.0)
        self.assertEqual(score_text("Go", task), 1.0)

    def test_forbidden_text_fails_score(self) -> None:
        task = EvaluationTask(
            task_id="instruction-003",
            category="instruction_adherence",
            prompt="Return READY without punctuation.",
            expected_contains=["READY"],
            expected_not_contains=["."],
        )

        self.assertEqual(score_text("READY.", task), 0.0)
        self.assertEqual(score_text("READY", task), 1.0)

    def test_contains_matching_still_supports_partial_credit(self) -> None:
        task = EvaluationTask(
            task_id="reasoning-001",
            category="reasoning",
            prompt="Return two facts.",
            expected_contains=["alpha", "beta"],
        )

        self.assertEqual(score_text("alpha only", task), 0.5)


class SuiteTests(unittest.TestCase):
    def test_tci_suite_has_five_challenging_tasks_per_category(self) -> None:
        suite = load_suite(PROJECT_ROOT / "evaluation-runner" / "suites" / "tci-v0.1.json")
        categories = {}
        for task in suite.tasks:
            categories.setdefault(task.category, 0)
            categories[task.category] += 1

        self.assertEqual(len(suite.tasks), 25)
        self.assertEqual(
            categories,
            {
                "reasoning": 5,
                "coding": 5,
                "mathematics": 5,
                "factual_knowledge": 5,
                "instruction_adherence": 5,
            },
        )
        self.assertTrue(any(task.exact_match for task in suite.tasks))
        self.assertTrue(any(task.expected_not_contains for task in suite.tasks))


class ResultPackageTests(unittest.TestCase):
    def test_builds_package_without_prompt_or_response_content(self) -> None:
        task = EvaluationTask(
            task_id="reasoning-001",
            category="reasoning",
            prompt="What comes next?",
            expected_contains=["4"],
        )
        result = EvaluationResult(
            task=task,
            success=True,
            score=1.0,
            latency_ms=120.0,
            input_tokens=5,
            output_tokens=7,
            error_category=None,
        )

        package = build_result_package(
            model_name="llama3.1:8b",
            model_revision="unknown",
            quantization="unknown",
            engine_version="0.1.0",
            hardware={
                "gpu": "unavailable",
                "gpu_count": 1,
                "driver": "unavailable",
                "cuda": "unavailable",
                "system_ram_gb": 1,
            },
            energy={
                "gpu_energy_wh": 0,
                "sampling_interval_ms": 1000,
                "average_power_w": 0,
                "peak_power_w": 0,
                "raw_power_samples": [],
            },
            suite_id="tci-v0.1",
            results=[result],
            runner_version="0.1",
        )

        serialized = json.dumps(package)

        self.assertEqual(package["schema_version"], "0.1")
        self.assertEqual(package["evaluation"]["completed_tasks"], 1)
        self.assertEqual(package["performance"]["input_tokens"], 5)
        self.assertIn("tci_v0_1", package["evaluation"]["scores"])
        raw_result = package["evaluation"]["raw_results"][0]
        self.assertEqual(raw_result["latency_ms"], 120.0)
        self.assertEqual(raw_result["input_tokens"], 5)
        self.assertEqual(raw_result["output_tokens"], 7)
        self.assertNotIn("What comes next?", serialized)
        self.assertNotIn("expected_contains", serialized)
        self.assertNotIn("prompt", serialized.lower())

    def test_validates_generated_package_against_schema(self) -> None:
        package = make_package()

        validate_result_package(package, PROJECT_ROOT / "schemas" / "evaluation-run.schema.json")

    def test_builds_tci_and_ipw_scores_when_energy_is_available(self) -> None:
        package = make_package(energy_wh=2.0)

        tci = package["evaluation"]["scores"]["tci_v0_1"]
        ipw = package["evaluation"]["scores"]["ipw_v0_1"]

        self.assertAlmostEqual(tci["final_score"], 25.0)
        self.assertEqual(tci["categories"]["reasoning"]["category_weight"], 0.25)
        self.assertEqual(tci["categories"]["reasoning"]["benchmarks"][0]["task_id"], "reasoning-001")
        self.assertAlmostEqual(tci["categories"]["reasoning"]["benchmarks"][0]["raw_benchmark_score"], 1.0)
        self.assertAlmostEqual(tci["categories"]["reasoning"]["benchmarks"][0]["normalized_benchmark_score"], 100.0)
        self.assertAlmostEqual(ipw["unscaled"], 12.5)
        self.assertAlmostEqual(ipw["displayed"], 12500.0)
        self.assertEqual(ipw["energy_scope"], "local_inference_hardware")
        self.assertEqual(ipw["energy_source"], "local_gpu_telemetry")

    def test_defers_ipw_when_energy_is_unavailable(self) -> None:
        package = make_package(energy_wh=0.0)
        ipw = package["evaluation"]["scores"]["ipw_v0_1"]

        self.assertEqual(ipw["status"], "deferred")
        self.assertEqual(ipw["energy_scope"], "local_inference_hardware")
        self.assertEqual(ipw["energy_source"], "unavailable")

    def test_schema_validation_rejects_extra_raw_result_fields(self) -> None:
        package = make_package()
        package["evaluation"]["raw_results"][0]["prompt"] = "private content"

        with self.assertRaises(SchemaValidationError):
            validate_result_package(package, PROJECT_ROOT / "schemas" / "evaluation-run.schema.json")

    def test_schema_validation_applies_tci_category_references(self) -> None:
        package = make_package()
        del package["evaluation"]["scores"]["tci_v0_1"]["categories"]["reasoning"]["category_score"]

        with self.assertRaises(SchemaValidationError):
            validate_result_package(package, PROJECT_ROOT / "schemas" / "evaluation-run.schema.json")

    def test_schema_validation_applies_ipw_one_of(self) -> None:
        package = make_package()
        package["evaluation"]["scores"]["ipw_v0_1"] = {"unscaled": 1.0}

        with self.assertRaises(SchemaValidationError):
            validate_result_package(package, PROJECT_ROOT / "schemas" / "evaluation-run.schema.json")


class MonitorTests(unittest.TestCase):
    def test_nvml_monitor_uses_partial_final_interval_for_energy(self) -> None:
        monitor = NvmlBackgroundMonitor(interval_s=10.0)
        monitor._samples = [make_sample(timestamp=datetime(2026, 7, 11, 12, 0, tzinfo=UTC), power_w=100.0)]
        monitor._ended_at = datetime(2026, 7, 11, 12, 0, 1, tzinfo=UTC)

        energy = monitor.energy()

        self.assertAlmostEqual(energy["gpu_energy_wh"], 100.0 / 3600.0)
        self.assertEqual(energy["raw_power_samples"][0]["interval_s"], 1.0)

    def test_nvml_monitor_takes_initial_sample_on_enter(self) -> None:
        monitor = NvmlBackgroundMonitor(interval_s=10.0)
        monitor._sampler = FakeSampler(power_w=80.0)

        with patch("telperia_runner.monitor.read_cpu_utilization_percent", return_value=0.0):
            with patch("telperia_runner.monitor.read_memory_used_mb", return_value=1024.0):
                with patch("telperia_runner.monitor.Thread", FakeThread):
                    with monitor:
                        self.assertEqual(len(monitor._samples), 1)


class EvaluateCliTests(unittest.TestCase):
    def test_cli_returns_clear_error_when_ollama_is_unavailable(self) -> None:
        module = load_evaluate_cli()
        original_argv = sys.argv
        try:
            with TemporaryDirectory() as tmpdir:
                sys.argv = [
                    "evaluate.py",
                    "--model",
                    "llama3.1:8b",
                    "--suite",
                    str(PROJECT_ROOT / "evaluation-runner" / "suites" / "tci-v0.1.json"),
                    "--output",
                    str(Path(tmpdir) / "run.json"),
                ]
                with patch.object(module, "OllamaClient", return_value=UnavailableClient()):
                    with redirect_stderr(StringIO()):
                        with self.assertRaises(SystemExit) as raised:
                            module.main()
        finally:
            sys.argv = original_argv

        self.assertEqual(raised.exception.code, 2)

    def test_run_evaluation_uses_post_run_energy_snapshot_for_ipw(self) -> None:
        suite = make_suite()
        energy_calls = 0

        def energy_snapshot() -> dict:
            nonlocal energy_calls
            energy_calls += 1
            return {
                "gpu_energy_wh": 2.0,
                "sampling_interval_ms": 1000,
                "average_power_w": 2.0,
                "peak_power_w": 2.0,
                "raw_power_samples": [],
            }

        package = run_evaluation(
            suite=suite,
            model_name="llama3.1:8b",
            client=FakeEvaluationClient(),
            hardware={
                "gpu": "NVIDIA Test GPU",
                "gpu_count": 1,
                "driver": "test",
                "cuda": "test",
                "system_ram_gb": 1,
            },
            energy=energy_snapshot,
        )

        self.assertEqual(energy_calls, 1)
        self.assertEqual(package["energy"]["gpu_energy_wh"], 2.0)
        self.assertIn("unscaled", package["evaluation"]["scores"]["ipw_v0_1"])


class FakeOpener:
    def open(self, request, timeout: float):
        body = json.loads(request.data.decode())
        assert body["model"] == "llama3.1:8b"
        assert body["prompt"] == "Say hello."
        assert body["options"]["num_predict"] == 64
        return FakeResponse(
            {
                "response": "hello",
                "prompt_eval_count": 3,
                "eval_count": 4,
            }
        )


class FakeErrorOpener:
    def open(self, request, timeout: float):
        return FakeResponse({"error": "model not found"})


class FakeUrlopen:
    def urlopen(self, target, timeout: float):
        assert target == "http://ollama.test/api/version"
        return FakeResponse({"version": "0.1.0"})


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


class FakeEvaluationClient:
    def version(self) -> str:
        return "0.1.0"

    def generate(self, model: str, prompt: str, max_output_tokens: int = 64):
        return type(
            "Generation",
            (),
            {
                "success": True,
                "text": "4",
                "latency_ms": 100.0,
                "input_tokens": 1,
                "output_tokens": 1,
                "error_category": None,
            },
        )()


class FakeThread:
    def __init__(self, target, daemon: bool) -> None:
        self.target = target
        self.daemon = daemon

    def start(self) -> None:
        return None

    def join(self) -> None:
        return None


class FakeSampler:
    def __init__(self, power_w: float) -> None:
        self.power_w = power_w
        self.shutdown_calls = 0

    def initialize(self) -> None:
        return None

    def shutdown(self) -> None:
        self.shutdown_calls += 1

    def read_gpu_metrics(self) -> GpuMetrics:
        return GpuMetrics(
            index=0,
            name="NVIDIA Test GPU",
            utilization_percent=10.0,
            vram_used_mb=512.0,
            vram_total_mb=8192.0,
            power_draw_w=self.power_w,
            temperature_c=50.0,
        )


class UnavailableClient:
    def version(self):
        raise ConnectionError("Ollama service is unavailable")


def load_evaluate_cli():
    path = RUNNER_ROOT / "evaluate.py"
    spec = __import__("importlib.util").util.spec_from_file_location("evaluate_cli", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load evaluate CLI")
    module = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_sample(timestamp: datetime, power_w: float) -> TelemetrySample:
    return TelemetrySample(
        timestamp=timestamp,
        node_id="local",
        gpu=GpuMetrics(
            index=0,
            name="NVIDIA Test GPU",
            utilization_percent=10.0,
            vram_used_mb=512.0,
            vram_total_mb=8192.0,
            power_draw_w=power_w,
            temperature_c=50.0,
        ),
        cpu_utilization_percent=0.0,
        system_memory_used_mb=1024.0,
        current_model=None,
        inference_engine="ollama",
        request_count=0,
        error_count=0,
    )


def make_suite():
    return type(
        "Suite",
        (),
        {
            "suite_id": "tci-v0.1",
            "tasks": [
                EvaluationTask(
                    task_id="reasoning-001",
                    category="reasoning",
                    prompt="What comes next?",
                    expected_contains=["4"],
                )
            ],
        },
    )()


def make_result(task_id: str, category: str, score: float, success: bool = True) -> EvaluationResult:
    task = EvaluationTask(
        task_id=task_id,
        category=category,
        prompt="What comes next?",
        expected_contains=["4"],
    )
    return EvaluationResult(
        task=task,
        success=success,
        score=score,
        latency_ms=120.0,
        input_tokens=5,
        output_tokens=7,
        error_category=None,
    )


def make_package(energy_wh: float = 0.0) -> dict:
    result = make_result(task_id="reasoning-001", category="reasoning", score=1.0)
    return build_result_package(
        model_name="llama3.1:8b",
        model_revision="unknown",
        quantization="unknown",
        engine_version="0.1.0",
        hardware={
            "gpu": "unavailable",
            "gpu_count": 1,
            "driver": "unavailable",
            "cuda": "unavailable",
            "system_ram_gb": 1,
        },
        energy={
            "gpu_energy_wh": energy_wh,
            "sampling_interval_ms": 1000,
            "average_power_w": energy_wh,
            "peak_power_w": energy_wh,
            "raw_power_samples": [],
        },
        suite_id="tci-v0.1",
        results=[result],
        runner_version="0.1",
    )


if __name__ == "__main__":
    unittest.main()
