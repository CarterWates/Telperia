# Telperia Docs Guide

## Read These Docs In This Order

This folder is organized so a new reader can move from the project purpose to the current Agent and backend work without guessing where to start.

## Contributors

1. `README.md`: project overview and current phase.
2. `docs/roadmap.md`: MVP phases and current sequencing.
3. `docs/phase-5-local-experiments.md`: local model testing workflow.
4. `docs/windows-test-contributor-runbook.md`: Windows NVIDIA testing and branch hygiene.
5. `SECURITY.md`: privacy, secret handling, upload review, and release checklist.

## Methodology Readers

1. `docs/telperia-methodology-v0.1.md`: plain-language methodology overview.
2. `methodology/TCI-v0.1.md`: current Telperia Capability Index formula.
3. `methodology/factual-reliability-v0.1.md`: factual reliability metrics.
4. `methodology/IPW-v0.1.md`: Local Intelligence-per-Watt formula and energy caveats.
5. `methodology/verification-levels.md`: evidence quality levels.
6. `methodology/deferred-metrics.md`: how to present TRI, Transparency Score, and other deferred metrics.
7. `methodology/TCI-v0.2-proposal.md`: proposal only, not current production scoring.

## Backend Work

1. `docs/phase-6-backend-design.md`: backend data model and access model.
2. `docs/result-ingestion-contract.md`: validation, privacy, duplicate, and storage contract.
3. `docs/result-ingestion-api.md`: request and response shapes for `POST /api/results/ingest`.
4. `apps/api/README.md`: how the local API skeleton wraps validation and how the future service connects Storage, summaries, and public review.
5. `docs/supabase-setup.md`: setup, environment variables, migration safety, and advisor checks.
6. `supabase/migrations/20260823000000_phase_6_result_ingestion.sql`: draft migration.

## Local Testing

1. `evaluation-runner/README.md`: local runner and telemetry commands.
2. `docs/phase-5-results-summary.md`: current seed results.
3. `tests/fixtures/ingestion/README.md`: ingestion validation fixtures.
4. `tests/fixtures/observatory/README.md`: public-safe Observatory row fixtures.
5. `docs/observatory-data-shape.md`: future public comparison row shape.

## Website Work

1. `apps/observatory-web/README.md`: static Observatory shell status and local opening instructions.
2. `apps/observatory-web/index.html`: current home, methodology, result table, detail, and status shell.
3. `tests/fixtures/observatory/README.md`: public-safe row fixture used by the shell.
4. `docs/observatory-data-shape.md`: contract for the public comparison fields.

## Agent Work

1. `agent/README.md`: local-first Agent scaffold, privacy defaults, and JSONL event export.
2. `schemas/inference-event.schema.json`: non-content inference event contract.
3. `schemas/telemetry-sample.schema.json`: shared non-content hardware telemetry sample contract.
4. `docs/telperia-methodology-v0.1.md`: Agent privacy modes and prohibited default collection.

Quick local checks:

```bash
python3 -m unittest discover -s tests -q
python3 -m compileall -q agent apps/api evaluation-runner tests
```

## Current Phase

Phase 8 has started with Step 26: separating the Telperia Agent from the Evaluation Runner. The repo now includes local validation, a runnable local API wrapper, API and backend contracts, a Supabase migration draft, a static Observatory shell, and a local-only Agent scaffold. Live Supabase deployment, hosted API wiring, continuous Agent monitoring, and site deployment are not implemented yet.
