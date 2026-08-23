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

The repository now includes early seed result packages, including Windows RTX 5070 NVML runs with calculated Local IPW. See `docs/phase-5-results-summary.md`.

## Methodology Proposal Status

TCI v0.1 remains the active MVP capability score. A separate TCI v0.2 proposal exists in `methodology/TCI-v0.2-proposal.md` for future benchmark and scoring improvements, but it is not implemented and should not be used for current result packages.

## Phase 6 Entry Gate

Backend work may begin after at least one Linux or Windows NVIDIA result package validates with nonzero GPU energy, raw power samples, Local IPW, methodology metadata, and verification metadata. Supabase/backend ingestion should preserve private-by-default uploads and explicit public opt-in.

## Phase 6 Backend Design

Phase 6 begins with the backend design in `docs/phase-6-backend-design.md`. The first backend implementation should validate local result packages, store raw JSON privately, extract public-safe summaries, and keep public submission as an explicit opt-in workflow.

The result ingestion contract is defined in `docs/result-ingestion-contract.md`. Backend implementation should follow that contract before adding public Observatory reads.
