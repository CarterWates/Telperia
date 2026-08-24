# Result Ingestion Contract

## Status

Phase 6 MVP contract. This document defines the expected behavior for accepting Telperia evaluation result packages into the backend. It is implementation guidance until the backend API, database migrations, and tests are added.

TCI v0.1 remains the active capability score. TCI v0.2 is proposal-only and must not be accepted as a current production score.

## Purpose

Result ingestion turns a local evaluation result package into:

- A private raw JSON artifact.
- A private owner-visible upload record.
- Queryable model, hardware, score, energy, and verification summaries.
- An optional public submission request when the user explicitly opts in.

The backend must preserve raw measurements and reject unsafe or invalid data before it enters the trusted Telperia dataset.

## Contract Summary

### Input

One JSON object matching `schemas/evaluation-run.schema.json`.

### Default Visibility

Every accepted upload starts as `private`.

### Authentication

MVP uploads require an authenticated user. Anonymous public uploads are deferred.

### Output

The ingestion service returns an ingestion record with:

- `upload_id`
- `run_id`
- `ingestion_status`
- `visibility`
- `validation_warnings`
- `public_submission_status` when requested

### Side Effects

Accepted uploads should:

1. Store the complete raw result package in private Storage.
2. Create or reuse model and hardware summary records.
3. Create an evaluation run summary.
4. Create score and energy summary fields.
5. Remain private unless the user explicitly requests public review.

Rejected uploads should:

1. Not create public records.
2. Not create accepted evaluation run summaries.
3. Return a stable rejection code and human-readable message.
4. Store no raw package unless a future private quarantine workflow is explicitly approved.

## Recommended Endpoint

```text
POST /api/results/ingest
```

Request body:

```json
{
  "result_package": {},
  "visibility": "private"
}
```

Allowed `visibility` values on ingest:

- `private`
- `submit_for_public_review`

The backend must not accept direct `public` visibility on first upload.

Invalid or direct-public visibility should return a stable `invalid_visibility` rejection.

## Accepted Result Package Versions

For the MVP:

- `schema_version`: `0.1`
- `methodology.version`: `0.1`
- `evaluation.suite`: `tci-v0.1`
- `evaluation.scores.tci_v0_1.methodology_version`: `TCI v0.1`

Unknown schema or methodology versions should be rejected until the backend explicitly supports them.

## Validation Pipeline

The ingestion service should validate in this order:

1. Confirm the request is authenticated.
2. Confirm the body contains one JSON result package.
3. Validate against `schemas/evaluation-run.schema.json`.
4. Apply Telperia privacy checks.
5. Apply metric consistency checks.
6. Apply energy consistency checks.
7. Apply storage-path and duplicate-run checks.
8. Store raw JSON privately.
9. Extract normalized summary records.
10. Return accepted status.

Validation must happen before public submission status can be created.

The local MVP validator lives at `evaluation-runner/telperia_runner/ingestion.py`. It is intentionally storage-free and network-free so the same checks can be reused by local tests, a future Supabase Edge Function, or a small server-side API wrapper.

The first API-facing request and response shapes are defined in `docs/result-ingestion-api.md`.

## Privacy Checks

Reject packages containing any keys intended to carry private content:

- `prompt`
- `prompts`
- `prompt_text`
- `response`
- `responses`
- `response_text`
- `content`
- `filename`
- `file_path`
- `environment`
- `env`
- `api_key`
- `token`
- `password`
- `secret`
- `hostname`
- `serial_number`

These checks are in addition to schema validation. They protect future schema versions, accidental extra fields, and malformed client submissions.

The backend may store task identifiers, category names, scores, latency, token counts, energy samples, methodology metadata, and verification metadata.

## Metric Consistency Checks

Reject packages when:

- `completed_tasks` is greater than `total_tasks`.
- `completion_ratio` does not match `completed_tasks / total_tasks` within a small rounding tolerance.
- TCI final score is outside `0` to `100`.
- Any category weight is outside `0` to `1`.
- Any category score is outside `0` to `100`.
- Any raw benchmark score is outside `0` to `1`.
- Any normalized benchmark score is outside `0` to `100`.
- Factual Reliability rates are outside `0` to `1`.
- Factual Reliability counts do not add up to `total_questions`.
- `error_count` is negative.

The backend should not recalculate TCI as a replacement for the package value during MVP ingestion. It may verify consistency and store both the package values and extracted summaries.

## Energy Consistency Checks

For calculated Local IPW:

- `energy.gpu_energy_wh` must be greater than `0`.
- `energy.energy_scope` must be `local_inference_hardware`.
- `energy.energy_source` must be `local_gpu_telemetry`.
- `energy.monitor_backend` must be `nvml`.
- `energy.raw_power_samples` must be present and nonempty.
- `evaluation.scores.ipw_v0_1.unscaled` must be present.
- `evaluation.scores.ipw_v0_1.displayed` must be present.
- Unscaled IPW should match `TCI * Completion Ratio / GPU Energy in Wh` within a small rounding tolerance.
- Displayed IPW should match `1000 * unscaled IPW` within a small rounding tolerance.

For deferred Local IPW:

- `evaluation.scores.ipw_v0_1.status` must be `deferred`.
- `evaluation.scores.ipw_v0_1.energy_source` must be `unavailable`.
- `energy.gpu_energy_wh` should be `0`.

Energy confidence metadata is optional for older packages. When present:

- `quality` must be one of `unavailable`, `low`, `medium`, or `high`.
- `sample_count` should equal the number of raw power samples.
- `measured_duration_s` should equal the sum of sample intervals when intervals are present.
- `warning_codes` should use known values from the schema.

Low energy confidence should not reject a package by itself. It should be stored as a warning for comparison and public display.

## Duplicate Handling

The backend should treat `run_id` as globally unique.

If an authenticated user uploads the same `run_id` twice:

- Return the existing accepted upload when the package hash matches.
- Reject the second upload when the package hash differs.

If a different user uploads the same `run_id`:

- Reject the upload unless a future signed-run or contributor workflow explicitly supports shared provenance.

## Raw Storage Contract

Recommended bucket:

```text
result-packages
```

Recommended path:

```text
users/{user_id}/runs/{run_id}.json
```

Storage rules:

- Raw result package objects are private.
- Object paths are generated by the backend, not trusted from the client.
- The backend should not allow overwrite by default.
- Public pages should use extracted public-safe summaries, not raw private Storage URLs.

## Extracted Summary Fields

The ingestion service should extract:

### Upload

- `user_id`
- `storage_path`
- `schema_version`
- `methodology_version`
- `evaluation_suite`
- `visibility`
- `ingestion_status`

### Model

- `model.name`
- `model.revision`
- `model.quantization`
- `runtime.engine`
- `runtime.engine_version`

### Hardware

- `hardware.gpu`
- `hardware.gpu_count`
- `hardware.driver`
- `hardware.cuda`
- `hardware.system_ram_gb`
- `run_environment.operating_system`
- `run_environment.monitor_backend`

### Evaluation Run

- `run_id`
- `timestamp`
- `run_environment.node_id`
- `completed_tasks`
- `total_tasks`
- `completion_ratio`
- `performance.error_count`
- `verification.level`
- `verification.runner_version`

### Scores

- `tci_v0_1.final_score`
- TCI category scores and weights
- Factual Reliability counts and rates
- Local IPW unscaled value when available
- Local IPW displayed value when available
- Local IPW deferred status and reason when unavailable

### Energy

- `gpu_energy_wh`
- `average_power_w`
- `peak_power_w`
- `sampling_interval_ms`
- `energy_scope`
- `energy_source`
- `monitor_backend`
- `energy_confidence.quality` when present
- `energy_confidence.warning_codes` when present

## Response Shapes

### Accepted Private Upload

```json
{
  "upload_id": "uuid",
  "run_id": "uuid",
  "ingestion_status": "accepted",
  "visibility": "private",
  "validation_warnings": []
}
```

### Accepted With Public Review Request

```json
{
  "upload_id": "uuid",
  "run_id": "uuid",
  "ingestion_status": "accepted",
  "visibility": "submitted_for_public_review",
  "public_submission_status": "pending_review",
  "validation_warnings": ["low_energy_confidence"]
}
```

### Rejected Upload

```json
{
  "ingestion_status": "rejected",
  "error_code": "invalid_schema",
  "message": "Result package failed schema validation."
}
```

## Stable Error Codes

- `unauthenticated`
- `invalid_request_body`
- `invalid_schema`
- `unsupported_schema_version`
- `unsupported_methodology_version`
- `unsupported_evaluation_suite`
- `privacy_violation`
- `metric_consistency_error`
- `energy_consistency_error`
- `duplicate_run_id`
- `storage_write_failed`
- `summary_write_failed`

## Warning Codes

Warnings should not reject otherwise valid private uploads.

- `low_energy_confidence`
- `energy_confidence_missing`
- `verification_level_zero`
- `ipw_deferred`
- `repeatability_not_established`

## Public Submission Rules

Public submission must be explicit.

The backend should only create a public submission record when:

- The upload is accepted.
- The authenticated owner requested public review.
- The upload is still owned by that user.
- The extracted public summary contains no disallowed private fields.

Public submission starts as `pending_review`. The MVP should not publish uploads automatically.

## Security Requirements

- Do not expose service-role credentials in public clients.
- Do not use user-editable metadata for authorization.
- Enable RLS on exposed tables.
- Use ownership predicates for private records.
- Use `WITH CHECK` on owner-controlled updates.
- Keep raw Storage objects private by default.
- Avoid user-controlled Storage paths.
- Avoid direct writes to Supabase `storage` schema tables.

## Implementation Test Checklist

When implementation begins, add tests for:

- Accepting a valid private result package.
- Accepting a valid result package with public review requested.
- Rejecting invalid schema data.
- Rejecting prompt or response content keys.
- Rejecting inconsistent completion ratio.
- Rejecting invalid IPW math.
- Accepting low energy confidence with a warning.
- Rejecting duplicate `run_id` with different package content.
- Preserving raw JSON separately from extracted summaries.
- Ensuring default visibility is private.

Implemented local validator coverage currently includes valid package acceptance, privacy key rejection, completion-ratio checks, IPW math checks, low energy-confidence warnings, missing energy-confidence warnings for older packages, and public-safe Observatory row extraction.
