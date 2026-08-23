# Phase 5 Local Experiments

## Purpose

Phase 5 turns the Phase 4 runner into repeatable local experiment evidence. The goal is to generate valid Telperia result packages while clearly separating local development smoke runs from results that can support public comparison.

The current `tci-v0.1` suite is a 25-task auto-gradable MVP suite. It is intended to challenge local models more than the initial smoke suite while still keeping Phase 5 reproducible. It is not yet a public frontier benchmark.

## Experiment Classes

### Local Development

Use this class for Mac runs, machines without NVML, or quick runner smoke tests.

- Hardware monitor: `disabled`
- Verification level: `0`
- Local IPW status: may be `deferred` when GPU energy is unavailable
- Public comparison: not eligible
- Purpose: confirm the runner, schema, scoring, and result package flow

### Supported NVIDIA Run

Use this class for Linux or Windows machines with an NVIDIA GPU and working NVML.

- Hardware monitor: `nvml`
- Verification level: `0` until a stronger verification process is approved
- Local IPW status: expected to include unscaled and displayed IPW
- Public comparison: candidate seed data after review
- Purpose: collect capability, reliability, performance, and energy evidence

### Mac Local Development

Use this class for Apple Silicon or Intel Mac runs until a separate Mac energy methodology is approved.

- Hardware monitor: `disabled`
- Verification level: `0`
- Local IPW status: `deferred`
- Public comparison: not eligible
- Purpose: confirm model capability, runner behavior, schema validation, and result package privacy without claiming GPU energy efficiency

### Sample Fixture

Use this class only for hand-authored or synthetic examples.

- Must be clearly labeled as sample data
- Must not be mixed with measured runs
- Must not be used for model ranking

## Naming Convention

Store local experiment outputs under `datasets/results/`.

Recommended filename format:

```text
YYYY-MM-DD_<model-slug>_<suite-id>_<run-class>_<run-number>.json
```

Example:

```text
2026-07-12_llama3-1-8b_tci-v0-1_local-dev_001.json
```

## Mac Local Development Command

Before running the evaluation, confirm Ollama is installed, running, and has the target model available:

```bash
ollama --version
ollama list
```

If the target model is missing, install it before a measured run:

```bash
ollama pull llama3.1:8b
```

Use this command when Ollama is available but NVML is not:

```bash
cd evaluation-runner
python3 evaluate.py \
  --model llama3.1:8b \
  --suite suites/tci-v0.1.json \
  --hardware-monitor disabled \
  --node-id local \
  --max-output-tokens 64 \
  --output ../datasets/results/2026-07-12_llama3-1-8b_tci-v0-1_local-dev_001.json
```

Expected result:

- The package validates against `schemas/evaluation-run.schema.json`.
- TCI v0.1 is present.
- Factual Reliability v0.1 is present.
- Local IPW v0.1 is deferred because GPU energy is unavailable.
- No prompt text or response text is saved.

## Linux NVIDIA Validation Command

Use this command on a supported Linux NVIDIA system:

```bash
cd evaluation-runner
python3 evaluate.py \
  --model llama3.1:8b \
  --suite suites/tci-v0.1.json \
  --hardware-monitor nvml \
  --node-id linux-laptop \
  --max-output-tokens 64 \
  --output ../datasets/results/2026-07-12_llama3-1-8b_tci-v0-1-nvml_001.json
```

Expected result:

- Raw power samples are present.
- GPU energy in Wh is greater than zero.
- Local IPW v0.1 includes both `unscaled` and `displayed`.
- Hardware metadata identifies the NVIDIA GPU and driver.

## Windows NVIDIA Validation Command

Use this command from PowerShell on a Windows machine with Ollama, Python, NVIDIA drivers, and NVML available:

```powershell
cd evaluation-runner
python evaluate.py `
  --model llama3.1:8b `
  --suite suites/tci-v0.1.json `
  --hardware-monitor nvml `
  --node-id windows-5070 `
  --max-output-tokens 64 `
  --output ../datasets/results/2026-08-23_llama3-1-8b_tci-v0-1_windows-nvml_001.json
```

Expected result:

- Raw power samples are present.
- GPU energy in Wh is greater than zero.
- Local IPW v0.1 includes both `unscaled` and `displayed`.
- `energy.monitor_backend` is `nvml`.
- `energy.energy_source` is `local_gpu_telemetry`.

## Review Checklist

Before keeping a result package in the repo, verify:

- The JSON validates against `schemas/evaluation-run.schema.json`.
- `schema_version` is `0.1`.
- `run_environment.node_id` is present and uses a user-chosen non-sensitive machine label.
- `methodology.version` is `0.1`.
- `verification.level` is present.
- `evaluation.scores.tci_v0_1.final_score` is present.
- `evaluation.scores.factual_reliability_v0_1` includes all required rates.
- `evaluation.scores.ipw_v0_1` is either calculated or explicitly deferred.
- `evaluation.scores.ipw_v0_1.energy_scope` is `local_inference_hardware`.
- `evaluation.raw_results` contains task ids, scores, latency, token counts, and errors.
- `energy.monitor_backend` is present.
- `energy.energy_scope` is `local_inference_hardware`.
- `energy.energy_source` is present.
- `energy.raw_power_samples` is present for NVML runs.
- No prompt text, response text, filenames, environment variables, tokens, passwords, or API keys are present.

Current reviewed result packages are summarized in `docs/phase-5-results-summary.md`.

## Publication Rule

Phase 5 results are preliminary. A result may be used as seed evidence only when its run class, hardware monitor, model metadata, methodology version, schema version, and verification level are clear. Local development results must not be presented as comparable public benchmark results.

Client-device power is not a valid proxy for hosted or data-center inference energy. Hosted IPW requires provider-side reported, estimated, or audited energy data in a future methodology version.
