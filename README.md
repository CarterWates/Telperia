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

Phases 1-5 established the MVP foundation, schemas, local telemetry prototype, evaluation runner, cross-platform local experiment flow, seed results, repeatability protocol, and energy confidence metadata support. Phase 6 is active and focused on private-by-default backend ingestion design before live Supabase implementation.

## What Works Today

- The local evaluation runner can run one Ollama model at a time.
- The default `tci-v0.1` suite contains 25 auto-gradable tasks.
- Result packages preserve raw benchmark scores, normalized scores, category weights, TCI, Factual Reliability, Local IPW status, telemetry metadata, energy confidence metadata for new runs, and verification metadata.
- Linux and Windows NVIDIA systems can use `--hardware-monitor nvml` when NVML is available.
- Mac and non-NVML machines can run with `--hardware-monitor disabled`; those runs defer Local IPW.
- Windows NVIDIA result packages are available under `datasets/results/`.
- A local ingestion validator can check result packages and extract public-safe Observatory rows before live backend upload code exists.
- A draft Supabase migration and ingestion fixtures are available for Phase 6 backend review.
- Public-safe Observatory row fixtures are available for Phase 7 website and API tests.
- Backend service design and Windows contributor runbook docs are available for future implementation and test runs.
- No prompt text or model response text is saved in result packages.

## Quick Local Check

Run these from the repository root:

```bash
python3 -m unittest discover -s tests -q
python3 -m compileall -q evaluation-runner tests
python3 evaluation-runner/evaluate.py --help
```

## Current Result Packages

- 1 Mac/local development result with Local IPW deferred.
- 11 Windows RTX 5070 NVML results with measured GPU energy and calculated Local IPW.

See `docs/phase-5-results-summary.md` for the current seed result table.

## Next Project Milestone

The next project milestone is implementing Phase 6 private-by-default result ingestion. More measured Phase 5 results can continue in parallel when a Windows or Linux NVIDIA machine is available.

- Mac development run: use `--hardware-monitor disabled --node-id local`.
- Linux NVIDIA run: use `--hardware-monitor nvml --node-id linux-laptop`.
- Windows NVIDIA repeat runs: use `--hardware-monitor nvml --node-id windows-5070`.

See `docs/phase-5-local-experiments.md` for the full commands and review checklist.

See `docs/README.md` for the recommended documentation reading order. Key Phase 6 docs include `apps/api/README.md`, `docs/phase-6-backend-design.md`, `docs/result-ingestion-contract.md`, `docs/result-ingestion-api.md`, `docs/observatory-data-shape.md`, `docs/supabase-setup.md`, `docs/windows-test-contributor-runbook.md`, `SECURITY.md`, and `docs/superpowers/plans/2026-08-23-phase-6-backend-ingestion.md`.
