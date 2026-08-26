# Result Ingestion API

## Status

Phase 6 API contract draft. This document defines the first backend-facing result ingestion interface before any hosted endpoint is deployed.

The local skeleton in `apps/api/telperia_api/ingestion_service.py` wraps the validator in `evaluation-runner/telperia_runner/ingestion.py` and implements the request/response shape without network or Supabase access. The future hosted API should add real authentication, duplicate persistence, private raw package storage, and summary writes.

## Endpoint

```text
POST /api/results/ingest
```

Required headers:

```text
Authorization: Bearer <user-access-token>
Content-Type: application/json
```

The endpoint requires an authenticated user. Anonymous uploads are not part of the Phase 6 MVP.

## Request Body

```json
{
  "result_package": {
    "schema_version": "0.1",
    "run_id": "11111111-1111-4111-8111-111111111111"
  },
  "visibility": "private"
}
```

Fields:

- `result_package`: one Telperia evaluation result package matching `schemas/evaluation-run.schema.json`.
- `visibility`: optional ingest request mode. Defaults to `private`.

Accepted `visibility` values:

- `private`
- `submit_for_public_review`

Rejected `visibility` values:

- `public`
- Any unknown value.

The backend owns public approval. A client cannot make a result public on first upload.

## Validation Flow

The endpoint should process requests in this order:

1. Confirm the request is authenticated.
2. Confirm the body is JSON.
3. Confirm the body contains exactly one `result_package`.
4. Set missing `visibility` to `private`.
5. Reject direct `public` visibility.
6. Run `validate_ingestion_package` from `evaluation-runner/telperia_runner/ingestion.py`.
7. Compute a canonical package hash for duplicate handling.
8. Check `run_id` ownership and package hash.
9. Store the raw result package in private Storage.
10. Write extracted model, hardware, run, score, and upload summaries.
11. Create a public submission row only when `visibility` is `submit_for_public_review`.
12. Return a stable response shape.

The local validator covers schema validation, privacy field rejection, score consistency, IPW math, energy confidence warnings, and Observatory summary extraction. The backend adds authentication, duplicate state, storage, and database writes.

## Accepted Private Upload

Response status: `201 Created`

```json
{
  "upload_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "run_id": "11111111-1111-4111-8111-111111111111",
  "ingestion_status": "accepted",
  "visibility": "private",
  "validation_warnings": ["low_energy_confidence", "verification_level_zero"]
}
```

## Accepted Public Review Request

Response status: `201 Created`

```json
{
  "upload_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "run_id": "11111111-1111-4111-8111-111111111111",
  "ingestion_status": "accepted",
  "visibility": "submitted_for_public_review",
  "public_submission_status": "pending_review",
  "validation_warnings": ["low_energy_confidence", "verification_level_zero"]
}
```

## Duplicate Upload

When the same authenticated user uploads the same `run_id` and the package hash matches an existing accepted upload, return the existing record instead of writing a duplicate.

Response status: `200 OK`

```json
{
  "upload_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "run_id": "11111111-1111-4111-8111-111111111111",
  "ingestion_status": "accepted",
  "visibility": "private",
  "duplicate": true,
  "validation_warnings": ["low_energy_confidence", "verification_level_zero"]
}
```

When the same authenticated user uploads the same `run_id` with different package content, reject it.

Response status: `409 Conflict`

```json
{
  "ingestion_status": "rejected",
  "error_code": "duplicate_run_id",
  "message": "A different result package already exists for this run_id."
}
```

Cross-user `run_id` collisions should also be rejected until Telperia has signed-run provenance.

## Rejected Uploads

### Invalid Request Body

Response status: `400 Bad Request`

```json
{
  "ingestion_status": "rejected",
  "error_code": "invalid_request_body",
  "message": "Request body must contain one result_package object."
}
```

### Invalid Schema

Response status: `422 Unprocessable Entity`

```json
{
  "ingestion_status": "rejected",
  "error_code": "invalid_schema",
  "message": "Result package failed schema validation."
}
```

### Privacy Violation

Response status: `422 Unprocessable Entity`

```json
{
  "ingestion_status": "rejected",
  "error_code": "privacy_violation",
  "message": "Result package contains a disallowed private content key."
}
```

### Metric Consistency Error

Response status: `422 Unprocessable Entity`

```json
{
  "ingestion_status": "rejected",
  "error_code": "metric_consistency_error",
  "message": "Result package metrics are internally inconsistent."
}
```

### Energy Consistency Error

Response status: `422 Unprocessable Entity`

```json
{
  "ingestion_status": "rejected",
  "error_code": "energy_consistency_error",
  "message": "Result package energy or Local IPW values are internally inconsistent."
}
```

### Unauthenticated

Response status: `401 Unauthorized`

```json
{
  "ingestion_status": "rejected",
  "error_code": "unauthenticated",
  "message": "Authentication is required to upload result packages."
}
```

## Stable Error Codes

- `unauthenticated`
- `invalid_request_body`
- `invalid_visibility`
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

## Stable Warning Codes

- `low_energy_confidence`
- `energy_confidence_missing`
- `verification_level_zero`
- `ipw_deferred`
- `repeatability_not_established`

Warnings do not reject otherwise valid private uploads. They should be preserved on upload records and exposed on public summaries when relevant.

## Storage And Summary Writes

For accepted uploads, store raw JSON privately at:

```text
result-packages/users/{user_id}/runs/{run_id}.json
```

Then write queryable summaries using the fields defined in `docs/observatory-data-shape.md`.

Rules:

- The backend generates `storage_path`.
- The client does not provide Storage paths.
- Raw package Storage objects remain private.
- Public Observatory rows use extracted summaries, not raw Storage URLs.
- Failed validation writes no accepted summary records.

## Public Approved Results

The local API also exposes an approved-only public read shape for Observatory development:

```text
GET /api/public/results
GET /api/public/results/{result_id_or_run_id}
```

These endpoints return public-safe summary fields shaped by `docs/observatory-data-shape.md`.

Rules:

- Private uploads are not returned.
- Pending public-review uploads are not returned.
- Rejected public submissions are not returned.
- Approved public submissions may be returned.
- Raw result packages and private Storage paths are never returned.
- Owner user ids, emails, prompt text, response text, filenames, hostnames, serial numbers, environment variables, tokens, passwords, API keys, and secrets are never returned.
- The API does not declare one universal winner; comparison and ranking logic belongs in explicit Observatory UI flows.

## Security Notes

- Do not accept prompt text or response text.
- Do not accept filenames, environment variables, hostnames, serial numbers, tokens, passwords, API keys, or secrets.
- Do not expose server-only credentials to browser code.
- Do not trust user-editable metadata for authorization.
- Apply RLS before exposing tables through public or authenticated clients.
- Keep direct summary writes behind the trusted backend path.
