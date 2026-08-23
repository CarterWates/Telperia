# Observatory Data Shape

## Status

Phase 6 MVP contract for public comparison data. This document defines the public-safe fields the backend should expose to the future Observatory website after a result package is accepted and approved for public display.

This is not a database migration or website implementation. It is the read model that Phase 6 backend work should prepare for Phase 7.

## Purpose

The Observatory should let users compare model configurations without exposing private upload details or raw user-owned files. Public comparison data should be small, consistent, filterable, and tied back to methodology and verification metadata.

## Source

Public Observatory rows are derived from accepted result packages that have passed ingestion and public review.

The source package remains the full raw JSON result package stored privately. The Observatory should read from extracted public-safe summary fields, not directly from private Storage objects.

## Public Comparison Fields

Each public comparison row should include:

| Field | Purpose |
| --- | --- |
| `result_id` | Public-safe result identifier. |
| `run_id` | Evaluation run identifier from the result package. |
| `model_name` | Model name, such as `gemma2:9b`. |
| `model_revision` | Model revision when available. |
| `quantization` | Quantization label when available. |
| `runtime_engine` | Runtime used for inference, such as `ollama`. |
| `runtime_version` | Runtime version when available. |
| `hardware_label` | Human-readable hardware summary. |
| `gpu` | GPU model or `unavailable`. |
| `gpu_count` | Number of GPUs used by the run. |
| `operating_system` | Operating system family. |
| `monitor_backend` | Energy monitor backend, such as `nvml` or `disabled`. |
| `tci_v0_1` | Final TCI v0.1 score. |
| `factual_correctness_rate` | Correct factual answers divided by total factual questions. |
| `factual_incorrect_answer_rate` | Incorrect factual answers divided by total factual questions. |
| `factual_abstention_rate` | Abstentions divided by total factual questions. |
| `factual_attempted_accuracy` | Correct answers divided by attempted factual answers. |
| `local_ipw_unscaled` | Unscaled Local IPW when available. |
| `local_ipw_displayed` | Scaled display Local IPW when available. |
| `local_ipw_status` | `calculated` or `deferred`. |
| `gpu_energy_wh` | Measured GPU energy in watt-hours when available. |
| `energy_confidence` | Energy confidence label. |
| `energy_warning_codes` | Machine-readable energy warnings. |
| `verification_level` | Telperia verification level. |
| `methodology_version` | Methodology version used by the result package. |
| `evaluation_suite` | Evaluation suite identifier. |
| `completed_tasks` | Completed task count. |
| `total_tasks` | Total task count. |
| `completion_ratio` | Completed tasks divided by total tasks. |
| `error_count` | Count of failed evaluation requests. |
| `result_timestamp` | Timestamp from the evaluation run. |
| `published_at` | Timestamp when the result became public. |

## Required MVP Columns

The first Observatory table needs these fields at minimum:

- Model name.
- Hardware label.
- TCI v0.1.
- Factual Reliability summary.
- Local IPW value or deferred status.
- Energy confidence.
- Verification level.
- Methodology version.

All other public fields support filtering, detail pages, and audit context.

## Display Rules

### Model

Display `model_name` as the primary model label. Add revision, quantization, and runtime details in the expanded row or detail view.

### Hardware

Display `hardware_label` as a compact summary, for example:

```text
NVIDIA GeForce RTX 5070 / Windows / NVML
```

If GPU telemetry is unavailable, make that clear:

```text
unavailable / macOS / disabled
```

### TCI

Display TCI as `TCI v0.1`. Do not mix TCI v0.1 and future TCI versions in the same unsplit leaderboard.

### Factual Reliability

Display the correctness rate first, with incorrect answer rate, abstention rate, and attempted accuracy available in expanded details.

### Local IPW

Display Local IPW only when calculated. If deferred, show the deferred status and reason instead of `0`.

Always preserve and expose the unscaled Local IPW value for detail views. The displayed Local IPW score is a scaled presentation value.

### Energy Confidence

Display energy confidence next to Local IPW. Low confidence should not hide the result, but it should visually warn users that energy/IPW comparisons are weaker.

Recommended labels:

- `unavailable`: no measured local GPU energy.
- `low`: measured energy exists, but the run was short or sparse.
- `medium`: measured energy meets MVP sample and duration thresholds.
- `high`: reserved for future stronger verification methods.

### Verification Level

Display verification level near the score, not buried in a detail page. Verification level explains evidence quality, not model capability.

## Public Detail Fields

A result detail page may include:

- TCI category scores and weights.
- Factual Reliability counts.
- Completion ratio.
- Token counts.
- Latency summary when available.
- Average and peak GPU power.
- GPU energy in Wh.
- Energy confidence warning codes.
- Evaluation suite.
- Runner version.
- Methodology document links.

The detail page should still avoid prompt text, response text, owner email, private Storage paths, filenames, hostnames, serial numbers, tokens, and secrets.

## Fields Not Exposed Publicly

The public Observatory should not expose:

- User email.
- User account id.
- Private raw Storage path.
- Prompt text.
- Response text.
- Uploaded filenames.
- Environment variables.
- API keys, tokens, passwords, or secrets.
- Hostnames.
- Device serial numbers.
- Local usernames.
- Any service-role or backend-only metadata.

## Sorts and Filters

Recommended MVP filters:

- Model name.
- GPU.
- Operating system.
- Monitor backend.
- Methodology version.
- Evaluation suite.
- Energy confidence.
- Verification level.
- Local IPW calculated vs deferred.

Recommended MVP sorts:

- TCI v0.1 descending.
- Local IPW displayed descending.
- Factual correctness rate descending.
- GPU energy Wh ascending.
- Result timestamp descending.
- Verification level descending.

Comparisons should default to grouping by similar hardware where possible. Cross-hardware comparisons are allowed only when the UI makes hardware differences obvious.

## Example Public Row

```json
{
  "result_id": "public_result_uuid",
  "run_id": "run_uuid",
  "model_name": "gemma2:9b",
  "model_revision": "unknown",
  "quantization": "unknown",
  "runtime_engine": "ollama",
  "runtime_version": "0.0.0",
  "hardware_label": "NVIDIA GeForce RTX 5070 / Windows / NVML",
  "gpu": "NVIDIA GeForce RTX 5070",
  "gpu_count": 1,
  "operating_system": "Windows",
  "monitor_backend": "nvml",
  "tci_v0_1": 56.0,
  "factual_correctness_rate": 0.8,
  "factual_incorrect_answer_rate": 0.2,
  "factual_abstention_rate": 0.0,
  "factual_attempted_accuracy": 0.8,
  "local_ipw_unscaled": 331.3671878951324,
  "local_ipw_displayed": 331367.1878951324,
  "local_ipw_status": "calculated",
  "gpu_energy_wh": 0.16899681696222224,
  "energy_confidence": "low",
  "energy_warning_codes": ["low_sample_count", "short_duration", "gross_energy_scope"],
  "verification_level": 0,
  "methodology_version": "0.1",
  "evaluation_suite": "tci-v0.1",
  "completed_tasks": 25,
  "total_tasks": 25,
  "completion_ratio": 1.0,
  "error_count": 0,
  "result_timestamp": "2026-08-23T00:00:00Z",
  "published_at": "2026-08-23T00:00:00Z"
}
```

## Relationship to Phase 6 Backend

Phase 6 backend work should create a public read path that can return this shape from approved summary data. The read path should not need to fetch raw private JSON for list views.

The future Phase 7 Observatory website can use this contract to build:

- Model comparison tables.
- Model detail pages.
- Hardware-filtered leaderboards.
- Energy confidence warnings.
- Methodology and verification badges.

Public-safe fixture rows for future website and API tests live in `tests/fixtures/observatory/public_rows.json`.
