# Telperia

Telperia is an open AI measurement project for understanding how AI systems perform, how reliable they are, how much energy they use, and how much evidence supports each claim.

The long-term goal is to build an AI Observatory where builders, researchers, companies, and local AI users can compare model configurations through transparent methodology, reproducible result packages, hardware metadata, verification levels, and energy-aware scores such as Local Intelligence-per-Watt.

This repository contains the MVP foundation for that system: methodology documents, schemas, a local evaluation runner, NVIDIA telemetry collection, and early result packages. The first release is planned as a web platform, evaluation runner, and lightweight telemetry agent. A native iOS application is not part of the MVP.

## MVP Objective

The MVP should allow a user to:

1. Visit the Telperia website.
2. Learn what TCI, TRI, IPW, and Factual Reliability measure.
3. Compare tested local AI model configurations.
4. View methodology, hardware, source, limitations, and verification level metadata behind every score.
5. Download the Telperia evaluation runner.
6. Evaluate a supported local model.
7. Measure GPU energy during evaluation.
8. Generate a standardized result package.
9. Upload the result privately or publicly.
10. Compare the result against similar hardware and model configurations.

## MVP Components

- `apps/observatory-web/`: public Observatory website.
- `apps/api/`: backend API and ingestion service.
- `evaluation-runner/`: controlled local benchmark runner.
- `agent/`: lightweight telemetry agent for normal model use.
- `methodology/`: versioned methodology and privacy documents.
- `schemas/`: result, telemetry, and inference event schemas.
- `datasets/`: benchmark and seed result data.
- `scripts/`: repository utilities.
- `tests/`: shared tests.

## Current Phase

Phases 1-4 are implemented for the MVP foundation, schemas, local telemetry prototype, and first evaluation runner. Phase 5 is active: local experiment protocol, cross-platform runner compatibility, and initial measured result collection come before backend ingestion.

## What Works Today

- The local evaluation runner can run one Ollama model at a time.
- The default `tci-v0.1` suite contains 25 auto-gradable tasks.
- Result packages preserve raw benchmark scores, normalized scores, category weights, TCI, Factual Reliability, Local IPW status, telemetry metadata, and verification metadata.
- Linux and Windows NVIDIA systems can use `--hardware-monitor nvml` when NVML is available.
- Mac and non-NVML machines can run with `--hardware-monitor disabled`; those runs defer Local IPW.
- The first Windows NVIDIA result package is available under `datasets/results/`.
- No prompt text or model response text is saved in result packages.

## Quick Local Check

Run these from the repository root:

```bash
python3 -m unittest discover -s tests -q
python3 -m compileall -q evaluation-runner tests
python3 evaluation-runner/evaluate.py --help
```

## Current Result Packages

- `2026-07-12_llama3-1-8b_tci-v0-1_local-dev_001.json`: Mac/local development result with Local IPW deferred.
- `2026-08-23_llama3-1-8b_tci-v0-1_windows-nvml_001.json`: Windows RTX 5070 result with NVML energy and calculated Local IPW.

## Next Experiment Runs

The next project milestone is collecting more measured Phase 5 results without starting backend ingestion prematurely.

- Mac development run: use `--hardware-monitor disabled --node-id local`.
- Linux NVIDIA run: use `--hardware-monitor nvml --node-id linux-laptop`.
- Windows NVIDIA repeat runs: use `--hardware-monitor nvml --node-id windows-5070`.

See `docs/phase-5-local-experiments.md` for the full commands and review checklist.
