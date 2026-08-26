# Phase 6 Backend Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the private-by-default Telperia result ingestion backend without weakening the current methodology, privacy rules, or public Observatory data contract.

**Architecture:** Keep validation and summary extraction as reusable Python logic first, then wrap it with Supabase-backed storage, database writes, and public review state. Raw result packages remain private. Public views use extracted summary fields only.

**Tech Stack:** Python validator, JSON schema in `schemas/evaluation-run.schema.json`, Supabase Postgres, Supabase Storage, Supabase Auth, RLS policies, and a server-side ingestion endpoint or Edge Function.

**Spec:** The source contracts are `docs/phase-6-backend-design.md`, `docs/result-ingestion-contract.md`, `docs/observatory-data-shape.md`, and `schemas/evaluation-run.schema.json`.

## Global Constraints

- TCI v0.1 remains the active production score.
- TCI v0.2 is proposal-only and must not be accepted as the current score.
- Raw benchmark, telemetry, and score details must remain separate from extracted public summaries.
- No prompt text, response text, filenames, environment variables, hostnames, serial numbers, API keys, tokens, passwords, or secrets may enter trusted storage.
- Upload visibility starts private. Public submission must be explicit and reviewed.
- Service-role credentials must stay server-side only.
- RLS must be enabled on exposed tables before any public or authenticated client access.
- Storage objects for raw result packages must be private by default.
- New backend behavior needs deterministic tests before it is treated as accepted.

---

## Task 1: Local Ingestion Validator

- [x] Add `evaluation-runner/telperia_runner/ingestion.py`.
- [x] Validate result packages against `schemas/evaluation-run.schema.json`.
- [x] Reject private content keys recursively while allowing token count metric fields.
- [x] Check accepted schema, methodology, suite, and TCI versions.
- [x] Check completion ratio, TCI ranges, benchmark normalization, Factual Reliability rates, and Local IPW math.
- [x] Treat missing energy confidence as a warning for older valid packages.
- [x] Extract a public-safe Observatory row matching `docs/observatory-data-shape.md`.
- [x] Add unit tests in `tests/test_ingestion.py`.

## Task 2: Supabase Project Readiness

- [x] Document how to reactivate or create the Supabase project.
- [x] Document local CLI, dashboard, migration, and advisor workflow.
- [x] Document frontend/public and server-only environment variable expectations.
- [ ] Confirm the project is not connected to any public client using server-only credentials.
- [x] Document the selected backend wrapper: local API app first, with Supabase wiring deferred.

## Task 3: Database Migration

- [x] Draft migration for `profiles`, `result_uploads`, `model_configs`, `hardware_profiles`, `evaluation_runs`, `run_scores`, and `public_submissions`.
- [x] Draft constraints for accepted visibility, ingestion status, public submission status, score ranges, and nonnegative energy values.
- [x] Draft indexes for owner lookup, public result listing, model lookup, hardware filtering, methodology version, and evaluation suite.
- [x] Store raw JSON in private Storage rather than public tables.
- [x] Avoid storing local usernames, hostnames, serial numbers, or upload filenames.

## Task 4: RLS And Storage Policies

- [x] Enable RLS on every exposed application table.
- [x] Allow authenticated users to read their own private uploads.
- [x] Allow authenticated users to create uploads only for themselves.
- [x] Allow authenticated users to request public review only for their own accepted uploads.
- [ ] Allow anonymous or public clients to read approved public summaries only.
- [x] Keep raw Storage objects private and owner-scoped.
- [ ] Avoid user-controlled Storage paths and overwrite behavior for the MVP.

## Task 5: Ingestion Endpoint

- [x] Accept one `result_package` JSON object per request.
- [x] Default visibility to `private`.
- [x] Allow `submit_for_public_review` but not direct `public` visibility.
- [x] Run the local ingestion validator before any storage or summary writes.
- [x] Hash the incoming package for duplicate handling.
- [x] Store raw JSON in `result-packages/users/{user_id}/runs/{run_id}.json`.
- [x] Write normalized model, hardware, run, score, and upload records in one server-side flow.
- [x] Return stable accepted and rejected response shapes from `docs/result-ingestion-contract.md`.

## Task 6: Duplicate Handling

- [x] Treat `run_id` as globally unique.
- [x] Return the existing accepted upload when the same owner submits identical content.
- [x] Reject the same owner submitting different content for the same `run_id`.
- [x] Reject cross-user `run_id` collisions until signed-run provenance exists.
- [x] Add tests for each duplicate path.

## Task 7: Public Review And Observatory Read Model

- [x] Create a public submission record only after validation succeeds.
- [x] Start submissions as `pending_review`.
- [ ] Add a read-only public summary query using fields from `docs/observatory-data-shape.md`.
- [ ] Ensure public summaries never read private raw Storage URLs.
- [ ] Include energy confidence and verification level in every public row.

## Task 8: Verification

- [ ] Run unit tests for validator, migrations, endpoint behavior, duplicate handling, and public summary extraction.
- [ ] Validate all existing `datasets/results/*.json` packages against the schema and local ingestion validator.
- [ ] Run a secret scan before pushing.
- [ ] Run Supabase database lints or advisors once the project is active.
- [ ] Update `README.md` and Phase 6 docs after each accepted backend milestone.
