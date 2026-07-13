# Telperia Result Packages

This folder is reserved for Phase 5 local experiment outputs and later seed result packages.

## Result Classes

- `local-dev`: Local smoke runs, including Mac runs with `--hardware-monitor disabled`. These confirm that the runner and schema work, but they are not public comparison data.
- `nvidia-nvml`: Runs from supported Linux NVIDIA systems with NVML telemetry. These are candidates for early seed data after review.
- `sample`: Synthetic or hand-authored examples. These must never be treated as measured benchmark results.
- `community-measured`: Future user-submitted results. These require backend and submission policy work before use.
- `telperia-verified`: Reserved for a future verification process. Do not use this label yet.

## File Naming

Use:

```text
YYYY-MM-DD_<model-slug>_<suite-id>_<run-class>_<run-number>.json
```

Example:

```text
2026-07-12_llama3-1-8b_tci-v0-1_local-dev_001.json
```

## Privacy Boundary

Result packages must not include prompt text, response text, filenames, environment variables, API keys, tokens, passwords, or private user content. Store task identifiers and measured outputs only.

## Review Before Commit

Before committing a result package:

- Validate it against `schemas/evaluation-run.schema.json`.
- Confirm the run class is clear.
- Confirm verification level is present.
- Confirm local-dev results are not described as public comparison data.
- Confirm NVML/Local IPW claims are backed by nonzero local GPU energy and raw power samples.
- Confirm local-dev results are not described as hosted or data-center energy measurements.
