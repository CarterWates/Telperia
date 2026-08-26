# Telperia MVP Roadmap

## Phase Order

1. Create the project foundation.
2. Define the data schemas.
3. Build the hardware telemetry prototype.
4. Build the evaluation runner.
5. Run initial local experiments.
   - Phase 5.1: make the local runner compatible with Linux NVIDIA, Windows NVIDIA, and Mac local-development workflows before backend ingestion.
6. Build the backend.
7. Build the Observatory website.
8. Build the Telperia Agent.
9. Build the personal node dashboard.
10. Add community submissions.
11. Seed the public Observatory.
12. Improve the platform.

## MVP Completion Definition

The Telperia MVP is complete when:

- The methodology is publicly documented.
- At least five model configurations have published results.
- Every score includes a methodology version.
- Every score includes a verification level.
- Every Local IPW result includes local inference hardware and energy data.
- The evaluation runner works on supported Linux NVIDIA and Windows NVIDIA systems when NVML is available.
- Mac local-development runs can generate valid capability result packages with Local IPW deferred.
- Users can generate a valid result package.
- Users can upload a result privately or publicly.
- The agent can collect non-content telemetry.
- Public model profiles can be compared.
- Raw measurements remain available for verification.
- Privacy modes are clear and functional.
- The platform clearly states its limitations.

## Phase 1 Boundary

Phase 1 creates repository structure and documentation only. It does not introduce app code, telemetry code, runner code, backend code, schema definitions, package dependencies, or scoring implementations.

## Phase 5.1 Boundary

Phase 5.1 makes local experiment collection portable before backend work begins. It supports measured Local IPW on Linux and Windows NVIDIA systems through NVML, supports Mac as a local-development capability run with IPW deferred, and keeps all energy source labels explicit. It does not implement hosted or data-center IPW.

## Phase 5 Data Status

The repository now includes early seed result packages, including Windows RTX 5070 NVML runs with calculated Local IPW and repeat runs for selected models. Phase 5 also added a repeatability protocol and runner support for energy confidence metadata so future Local IPW evidence can be interpreted honestly. See `docs/phase-5-results-summary.md` and `docs/phase-5-local-experiments.md`.

## Methodology Proposal Status

TCI v0.1 remains the active MVP capability score. A separate TCI v0.2 proposal exists in `methodology/TCI-v0.2-proposal.md` for future benchmark and scoring improvements, but it is not implemented and should not be used for current result packages.

TRI v0.1 and Transparency Score v0.1 are deferred. Phase 7 website work may explain TRI as a planned reliability metric and may show Transparency Evidence fields, but it must not publish numeric TRI or Transparency Score values until those methodologies are approved. See `methodology/deferred-metrics.md`.

## Phase 6 Entry Gate

Backend work may begin because `main` now contains validated Windows NVIDIA result packages with nonzero GPU energy, raw power samples, Local IPW, methodology metadata, and verification metadata. New runner output also includes energy confidence metadata for future ingested runs. Supabase/backend ingestion should preserve private-by-default uploads and explicit public opt-in.

## Phase 6 Backend Design

Phase 6 local backend foundation is in place. It began with the backend design in `docs/phase-6-backend-design.md`. The first backend implementation validates local result packages, stores raw JSON separately in local persistence, extracts public-safe summaries, and keeps public submission as an explicit opt-in workflow.

The result ingestion contract is defined in `docs/result-ingestion-contract.md`. Backend implementation should follow that contract before adding public Observatory reads.

The public Observatory comparison data shape is defined in `docs/observatory-data-shape.md`, including model, hardware, TCI, Factual Reliability, Local IPW, energy confidence, verification level, and methodology version fields.

The local API skeleton, local SQLite persistence path, local approved-results read path, and core Supabase migration foundation are in place for review. The backend can validate an upload, store raw JSON separately from public-safe summaries, persist normalized model and hardware rows, persist accepted run and score summaries, create a pending public submission request, and return only approved public summaries for Observatory development. It does not connect to live Supabase yet, and the migration has not been applied to a live Supabase project.

## Phase 7 Static Shell

An initial static Observatory shell exists in `apps/observatory-web/`. It includes homepage positioning, a public model directory, methodology overview, seed result comparison, result detail, and current status sections using local public-safe fixture data derived from `datasets/results/`.

Phase 7 Step 21 homepage wording now explains Telperia, why capability alone is insufficient, TCI, Factual Reliability, Local IPW, verification levels, planned TRI, Transparency Evidence, and the private-by-default contribution flow.

Phase 7 Step 22 model directory work groups public result rows by model and shows model name, conservative provider/open-status placeholders, representative TCI v0.1, Factual Reliability, Transparency Evidence, available Local IPW, verification level, and methodology version.

Phase 7 Step 23 model profile work adds a public-safe profile view for each model. Profiles aggregate approved seed evidence into TCI category breakdowns, Factual Reliability breakdowns, hardware-specific Local IPW runs, throughput, energy, verification, methodology, limitations, and a disabled result-package download placeholder until reviewed public package access exists.

Phase 7 Step 24 comparison work adds a public-safe comparison view for selecting two to four model/hardware configurations. It compares TCI, reasoning, coding, mathematics, Factual Reliability, incorrect and abstention rates, Transparency Evidence, Local IPW, GPU energy, latency, tokens per second, peak VRAM, verification level, and methodology version without assigning one universal winner. Latency and peak VRAM are marked deferred/not collected where current result packages do not include them.

Phase 7 Step 25 methodology page work publishes official Observatory methodology sections for TCI v0.1, Factual Reliability v0.1, Local IPW v0.1, Verification Levels, Privacy Policy, and Known Limitations. It also describes TRI v0.1 and Transparency Score v0.1 as planned/not yet scored, keeps current public language on Transparency Evidence, links score-like labels in the website back to methodology anchors, and includes in-page terminology explanations for the core scoring and result-package terms.

This shell is not deployed and does not read from Supabase yet. It should become the public Observatory frontend after Phase 6 backend ingestion can persist and expose approved summary rows.

## Phase 8 Agent Foundation

Phase 8 Step 26 separates the Telperia Agent from the Evaluation Runner. The Evaluation Runner remains responsible for controlled benchmark sessions and result packages. The Agent is now a separate local-first program under `agent/` for normal-use, non-content inference and telemetry records.

The first Agent CLI can write one schema-valid inference event to a local JSONL file. It defaults to private/local-only behavior, does not connect to Supabase, does not upload data, and keeps Research Contribution Mode disabled. The Agent imports shared telemetry types from `evaluation-runner/telperia_telemetry` so hardware telemetry structures can be reused without turning the runner into a continuous background process.

Phase 8 Step 27 adds the first Agent v0.1 local collection records. The Agent can now write local JSONL snapshots containing a non-content inference event, a hardware telemetry sample, and environment metadata such as operating system, inference engine, runtime version, quantization, and GPU/driver/CUDA fields when known. Unsupported GPU telemetry is represented as unavailable rather than inferred, which keeps Mac and non-NVIDIA records honest.

Phase 8 Step 28 adds explicit privacy modes. Private Mode is active and default. Personal Cloud Mode and Research Contribution Mode are recognized as planned modes, but neither can upload data until backend/cloud support is approved and connected. Research Contribution Mode remains disabled by default and requires explicit opt-in even to inspect its planned status.

Step 29 should build the next layer of Agent behavior: a local event loop or monitor boundary, plus clearer local configuration for future opt-in contribution without collecting prompt or response content.
