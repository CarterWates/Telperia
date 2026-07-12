# Telperia

Telperia is an MVP for transparent measurements of local AI model capability, reliability, efficiency, and verification metadata.

The first release is planned as a web platform, evaluation runner, and lightweight telemetry agent. A native iOS application is not part of the MVP.

## MVP Objective

The MVP should allow a user to:

1. Visit the Telperia website.
2. Learn what TCI, TRI, IPW, and Factual Reliability measure.
3. Compare tested local AI model configurations.
4. View methodology, hardware, source, limitations, and verification level metadata behind every score.
5. Download the Telperia evaluation runner.
6. Evaluate a supported local model.
7. Measure GPU energy during evaluation.
8. Generate a standardized result package.
9. Upload the result privately or publicly.
10. Compare the result against similar hardware and model configurations.

## MVP Components

- `apps/observatory-web/`: public Observatory website.
- `apps/api/`: backend API and ingestion service.
- `evaluation-runner/`: controlled local benchmark runner.
- `agent/`: lightweight telemetry agent for normal model use.
- `methodology/`: versioned methodology and privacy documents.
- `schemas/`: result, telemetry, and inference event schemas.
- `datasets/`: benchmark and seed result data.
- `scripts/`: repository utilities.
- `tests/`: shared tests.

## Current Phase

Phases 1-4 are implemented for the MVP foundation, schemas, local telemetry prototype, and first evaluation runner. Phase 5 is in preparation: local experiment protocol and seed result structure come before initial measured runs.
