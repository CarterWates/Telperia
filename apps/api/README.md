# Phase 6 API Service

## Status

Local Phase 6 API skeleton for result ingestion. This folder contains a service module, local persistence adapters, and a runnable local HTTP API that wrap the local result validator and return the same response shape expected by the future hosted endpoint.

The Phase 6 API should wrap the local result validator, write private raw packages to Supabase Storage, store queryable summaries in Postgres, and create public review requests only when the user explicitly asks for them.

## Source Contracts

- `docs/result-ingestion-api.md`: request and response contract.
- `docs/result-ingestion-contract.md`: validation, privacy, duplicate, and storage behavior.
- `docs/observatory-data-shape.md`: public comparison row shape.
- `docs/supabase-setup.md`: setup, migration, and advisor workflow.
- `evaluation-runner/telperia_runner/ingestion.py`: local validation and public-safe summary extraction.
- `supabase/migrations/20260823000000_phase_6_result_ingestion.sql`: draft database and Storage migration.

## Recommended Shape

The future hosted service should expose:

```text
POST /api/results/ingest
```

The endpoint should accept one result package and an optional visibility mode:

- `private`
- `submit_for_public_review`

It must reject direct `public` visibility. Public publishing is a review state, not an upload setting.

## Local Skeleton

The local service lives in:

```text
apps/api/telperia_api/ingestion_service.py
```

It currently provides:

- `ingest_result_request`: backend-shaped request handling for one result package.
- `InMemoryIngestionStore`: local duplicate handling for tests and CLI usage.
- `SQLiteIngestionStore`: local durable persistence for accepted uploads, raw packages, normalized summaries, and public-review requests.
- Canonical package hashing.
- Private Storage path generation.
- Local validation through `evaluation-runner/telperia_runner/ingestion.py`.
- Public-safe Observatory summary extraction for accepted records.

The runnable local HTTP wrapper lives in:

```text
apps/api/telperia_api/http_app.py
```

It exposes:

- `GET /health`
- `POST /api/results/ingest`
- `GET /api/public/results`
- `GET /api/public/results/{result_id_or_run_id}`

It does not write to Supabase. Accepted uploads can be stored in memory or in a local SQLite database. SQLite mode keeps Phase 6 persistence testable on a Mac before live infrastructure is connected.

## Run Locally

From the repository root:

```bash
PYTHONPATH=apps/api:evaluation-runner python3 -m telperia_api.http_app --host 127.0.0.1 --port 8000
```

Run with local SQLite persistence:

```bash
PYTHONPATH=apps/api:evaluation-runner python3 -m telperia_api.http_app \
  --host 127.0.0.1 \
  --port 8000 \
  --sqlite-db .local/telperia-api.db
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Validate and ingest a fixture locally:

```bash
python3 - <<'PY' > /tmp/telperia-ingest-fixture.json
import json
from pathlib import Path

package = json.loads(Path("tests/fixtures/ingestion/valid_private_upload.json").read_text())
print(json.dumps({"result_package": package}))
PY

curl -X POST http://127.0.0.1:8000/api/results/ingest \
  -H 'Content-Type: application/json' \
  -H 'X-Telperia-User-Id: local-dev-user' \
  --data-binary @/tmp/telperia-ingest-fixture.json
```

The `X-Telperia-User-Id` header is a local-only stand-in for future authenticated user identity. It is not real authentication and should not be used for hosted deployments.

## Ingestion Flow

1. Resolve the local user identity placeholder. Hosted deployments should replace this with authenticated user identity.
2. Parse exactly one result package from the request body.
3. Run `validate_ingestion_package` from `evaluation-runner/telperia_runner/ingestion.py`.
4. Reject packages with invalid schema, privacy violations, broken metric math, broken Local IPW math, or unsupported versions. Accepted packages must contain no prompt or response content.
5. Create a canonical package hash for duplicate checks.
6. Reject reused `run_id` values when package content differs.
7. Store raw JSON privately in the `result-packages` bucket.
8. Insert or reuse model and hardware summary records.
9. Insert the evaluation run and score summaries.
10. If requested, insert a `public_submissions` row with `pending_review`.
11. Return the response shape from `docs/result-ingestion-api.md`.

## Storage

Raw result packages should be written to:

```text
result-packages/users/{user_id}/runs/{run_id}.json
```

Rules:

- Backend code generates the path.
- Clients do not submit Storage paths.
- Raw objects stay private.
- Public pages read extracted summaries, not raw Storage URLs.
- Failed validation writes no accepted summaries.

In SQLite development mode, raw package JSON is stored in `raw_result_packages`; queryable upload, model, hardware, run, score, and review fields are stored in separate summary tables. This mirrors the future Supabase separation without requiring credentials.

## Public Read Path

The local public read path returns approved Observatory summaries only:

```bash
curl http://127.0.0.1:8000/api/public/results
curl http://127.0.0.1:8000/api/public/results/<result-id-or-run-id>
```

Rules:

- Private uploads are hidden.
- Pending public-review uploads are hidden.
- Rejected public submissions are hidden.
- Approved submissions return public-safe fields from `docs/observatory-data-shape.md`.
- Public responses never include raw result packages, private Storage paths, owner ids, prompt text, response text, filenames, hostnames, serial numbers, environment variables, tokens, passwords, API keys, or secrets.

## Database Access

The migration draft enables RLS and keeps trusted summary writes behind the future backend path. The local SQLite adapter mirrors the same table responsibilities for development and tests, but it is not a replacement for Supabase RLS.

The service should write:

- `result_uploads`
- `model_configs`
- `hardware_profiles`
- `evaluation_runs`
- `run_scores`
- `public_submissions` when public review is requested

The public Observatory should only read approved public summaries.

## Security Rules

- Do not expose server-only credentials to browser code.
- Do not trust user-editable metadata for authorization.
- Do not collect prompt or response content.
- Do not collect filenames, environment variables, hostnames, serial numbers, tokens, passwords, API keys, or secrets.
- Run Supabase advisors before applying migrations to production.
- Keep RLS enabled on exposed tables.

## Not Implemented Yet

- Supabase client wiring.
- Auth/session handling.
- Live Storage writes.
- Reviewer/admin workflow.
- Live Supabase public Observatory read endpoint.
- FastAPI or deployed hosted wrapper.

Those pieces should be added after the Supabase project is active and the migration has been tested locally or in staging.
