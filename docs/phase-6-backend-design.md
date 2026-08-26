# Phase 6 Backend Design

## Status

Phase 6 backend design for the Telperia MVP. The local API wrapper, SQLite persistence path, approved-results read path, and first Supabase migration foundation exist in the repo, but the migration has not been applied to a live Supabase project.

The Phase 6 backend should accept local evaluation result packages, keep uploads private by default, validate every package before ingestion, and expose only explicitly public results to the future Observatory.

## Goals

- Store complete evaluation result packages without losing raw measurements.
- Extract summary fields needed for filtering, comparison, and public model pages.
- Keep private uploads private unless the user explicitly opts in to public submission.
- Preserve methodology version, schema version, verification level, and energy confidence.
- Reject result packages that contain prompt text, response text, secrets, impossible measurements, or invalid schema data.
- Keep hosted/data-center IPW separate from Local IPW.

## Non-Goals

- Do not implement hosted API or data-center energy estimation in Phase 6.
- Do not calculate TCI v0.2; it remains proposal-only.
- Do not store user environment variables, filenames, hostnames, serial numbers, prompts, or responses.
- Do not publish community submissions without explicit opt-in and review status.
- Do not build the public Observatory UI in Phase 6.

## Backend Shape

The recommended MVP backend is Supabase with:

- Postgres for structured metadata and queryable summaries.
- Storage for raw result package JSON files.
- Auth for private user uploads.
- Row Level Security on all user-owned and submission tables.
- Server-side ingestion for schema validation and derived summary extraction.

Supabase guidance checked during design:

- Supabase recommends enabling RLS on tables in exposed schemas and using policies with explicit `TO` roles plus ownership predicates.
- Supabase Storage access is also controlled through RLS policies on `storage.objects`.
- Storage upsert needs more than insert-only access, so the MVP should avoid user-side overwrite behavior unless policies are deliberately expanded.
- Service-role keys must never be exposed in public clients.

References:

- <https://supabase.com/docs/guides/database/postgres/row-level-security>
- <https://supabase.com/docs/guides/storage/security/access-control>
- <https://supabase.com/docs/guides/storage/security/ownership>

## Data Model

### profiles

Purpose: one row per authenticated user profile. This table should contain only application-safe account metadata.

Suggested fields:

- `user_id uuid primary key references auth.users(id)`
- `display_name text`
- `created_at timestamptz`

Notes:

- Do not use editable user metadata for authorization.
- Authorization data should live in trusted server-side metadata or dedicated tables.

### result_uploads

Purpose: private user-owned upload records.

Suggested fields:

- `id uuid primary key`
- `user_id uuid not null references auth.users(id)`
- `storage_path text not null`
- `schema_version text not null`
- `methodology_version text not null`
- `evaluation_suite text not null`
- `visibility text not null default 'private'`
- `ingestion_status text not null`
- `validation_error text`
- `created_at timestamptz`
- `updated_at timestamptz`

Allowed visibility values:

- `private`
- `submitted_for_public_review`
- `public`

Allowed ingestion status values:

- `pending`
- `accepted`
- `rejected`

### model_configs

Purpose: normalized model identity for search and comparison.

Suggested fields:

- `id uuid primary key`
- `model_name text not null`
- `model_revision text not null`
- `quantization text not null`
- `runtime_engine text not null`
- `runtime_version text not null`
- `created_at timestamptz`

Uniqueness should include model name, revision, quantization, runtime engine, and runtime version.

### hardware_profiles

Purpose: normalized local hardware context.

Suggested fields:

- `id uuid primary key`
- `gpu text not null`
- `gpu_count integer not null`
- `driver text not null`
- `cuda text not null`
- `system_ram_gb numeric not null`
- `operating_system text not null`
- `monitor_backend text not null`
- `created_at timestamptz`

This should not store hostnames, serial numbers, local usernames, or automatic machine identifiers.

### evaluation_runs

Purpose: queryable summary of each accepted result package.

Suggested fields:

- `id uuid primary key`
- `upload_id uuid not null references result_uploads(id)`
- `model_config_id uuid not null references model_configs(id)`
- `hardware_profile_id uuid not null references hardware_profiles(id)`
- `run_id uuid not null`
- `timestamp timestamptz not null`
- `node_id text not null`
- `schema_version text not null`
- `methodology_version text not null`
- `evaluation_suite text not null`
- `completed_tasks integer not null`
- `total_tasks integer not null`
- `completion_ratio numeric not null`
- `error_count integer not null`
- `verification_level integer not null`
- `is_public boolean not null default false`
- `created_at timestamptz`

Suggested indexes:

- `user_id` through `result_uploads`
- `model_config_id`
- `hardware_profile_id`
- `is_public`
- `methodology_version`
- `evaluation_suite`

### run_scores

Purpose: queryable score summary while preserving raw JSON separately.

Suggested fields:

- `evaluation_run_id uuid primary key references evaluation_runs(id)`
- `tci_v0_1 numeric`
- `factual_correctness_rate numeric`
- `factual_incorrect_answer_rate numeric`
- `factual_abstention_rate numeric`
- `factual_attempted_accuracy numeric`
- `local_ipw_unscaled numeric`
- `local_ipw_displayed numeric`
- `local_ipw_status text`
- `gpu_energy_wh numeric`
- `average_power_w numeric`
- `peak_power_w numeric`
- `energy_source text`
- `energy_scope text`
- `energy_confidence text`
- `energy_warning_codes text[]`
- `tokens_per_second numeric`

### public_submissions

Purpose: review state for public Observatory publishing.

Suggested fields:

- `id uuid primary key`
- `evaluation_run_id uuid not null references evaluation_runs(id)`
- `submitted_by uuid not null references auth.users(id)`
- `status text not null`
- `review_notes text`
- `created_at timestamptz`
- `reviewed_at timestamptz`

Allowed statuses:

- `pending_review`
- `approved`
- `rejected`

## Storage

Recommended bucket:

- `result-packages`

Recommended object path:

```text
users/{user_id}/runs/{run_id}.json
```

Rules:

- Store the complete original result package JSON.
- Do not allow public bucket access for raw uploads.
- Avoid upsert in the MVP unless replacement policies are intentionally added.
- Public Observatory pages should use extracted approved fields, not direct raw object URLs by default.

## Ingestion Flow

1. Authenticated user uploads a result package.
2. Backend validates the JSON against `schemas/evaluation-run.schema.json`.
3. Backend rejects packages with prompt or response content fields.
4. Backend rejects impossible measurements such as negative energy, invalid percentages, or completed tasks greater than total tasks.
5. Backend stores the raw JSON in private Storage.
6. Backend creates a `result_uploads` row with `private` visibility.
7. Backend extracts model, hardware, run, score, energy, performance, methodology, and verification summaries into queryable tables.
8. User may explicitly submit a private upload for public review.
9. Approved public submissions become visible to the Observatory through public-safe summary records.

The detailed request, validation, extraction, response, and error-code contract is defined in `docs/result-ingestion-contract.md`.

The first reusable local implementation is `evaluation-runner/telperia_runner/ingestion.py`. It validates packages and extracts the public-safe Observatory row without performing authentication, Storage writes, database writes, or network calls.

The local API can now persist accepted uploads through `SQLiteIngestionStore` for development and tests. This stores raw package JSON separately from normalized upload, model, hardware, run, score, and public-review summary tables. Supabase Storage/Postgres wiring remains a future hosted-backend step.

The local API also exposes approved-only public summary reads for Observatory development. Private uploads, pending public-review uploads, and rejected public submissions are hidden from those public reads.

The future API wrapper responsibilities are summarized in `apps/api/README.md`.

## Validation Rules

The ingestion layer should require:

- Valid schema version.
- Valid methodology version.
- Valid evaluation suite identifier.
- TCI v0.1 data when current MVP scoring is used.
- Factual Reliability v0.1 data.
- Local IPW either calculated with positive measured GPU energy or explicitly deferred.
- Raw power samples when Local IPW is calculated.
- Energy scope and source labels.
- Energy confidence metadata when generated by newer runners.
- Verification metadata.

The ingestion layer should reject:

- Prompt text.
- Response text.
- Environment variables.
- API keys, tokens, or private keys.
- Hostnames, serial numbers, or local usernames.
- Negative energy or power values.
- Invalid completion ratios.
- Unknown public visibility states.

## Access Model

Default access should be:

- Owners can read their own uploads.
- Owners can upload new result packages.
- Owners can request public review for their own accepted uploads.
- Public users can read only approved public summary rows.
- Raw private result package files are not public.
- Admin/reviewer access is handled separately and should not rely on user-editable metadata.

RLS policy implementation should:

- Use `TO authenticated` for user-owned policies.
- Combine role checks with ownership checks using `(select auth.uid()) = user_id`.
- Use both `USING` and `WITH CHECK` for updates.
- Keep service-role access server-side only.
- Avoid `SECURITY DEFINER` functions unless there is a documented reason and they live outside exposed schemas.

## Public Observatory Projection

The public Observatory should read from approved summary data containing:

- Model name.
- Model revision or version.
- Quantization.
- Runtime engine and version.
- GPU and operating system.
- TCI v0.1.
- Factual Reliability metrics.
- Local IPW status and values.
- GPU energy in Wh.
- Energy confidence and warning codes.
- Verification level.
- Methodology version.
- Evaluation suite version.
- Result timestamp.

The public projection should not expose owner email, private raw object path, prompt text, response text, local filenames, hostnames, or tokens.

The detailed public comparison shape is defined in `docs/observatory-data-shape.md`.

## Phase 6 Build Order

1. Create a Supabase project or reactivate the paused project.
2. Confirm Supabase CLI or MCP access.
3. Use the local validator in `evaluation-runner/telperia_runner/ingestion.py` as the server-side validation baseline.
4. Create the initial migration for tables, indexes, RLS, and Storage bucket policies. Done in `supabase/migrations/20260823000000_phase_6_result_ingestion.sql`.
5. Add server-side ingestion validation by wrapping the local contract checks. Done in the local API wrapper.
6. Add tests with valid and rejected result packages. Done for local API and SQLite persistence.
7. Add a private upload path. Done locally with generated `result-packages/users/{user_id}/runs/{run_id}.json` paths.
8. Add public submission request and review status. Done locally with pending-review records.
9. Add a read-only public summary query for Phase 7 Observatory work. Done locally through SQLite public read methods and local HTTP endpoints.
10. Shape approved public summaries according to `docs/observatory-data-shape.md`. Done locally for the MVP public comparison fields.

The implementation sequence is tracked in `docs/superpowers/plans/2026-08-23-phase-6-backend-ingestion.md`.

## Open Decisions

- Whether Phase 6 ingestion should use an Edge Function, a small API app, or both.
- Whether raw JSON should be stored only in Storage or also duplicated in a Postgres `jsonb` column for audit convenience.
- Whether public review is manual-only for MVP or semi-automatic for verification level `0` results.
- Whether anonymous users can view public summaries before the full Observatory site is built.
