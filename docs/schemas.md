# Schemas

Telperia schemas define the portable data contracts used by the runner, telemetry sampler, agent, backend, and public Observatory.

## Files

- `schemas/evaluation-run.schema.json` describes one complete local evaluation result package.
- `schemas/telemetry-sample.schema.json` describes one non-content hardware telemetry sample.
- `schemas/inference-event.schema.json` describes one non-content inference event. The Phase 8 Agent writes this event shape locally as JSONL.

Evaluation run packages may include `run_environment` metadata with a user-chosen `node_id`, operating system family, and monitor backend. Energy blocks may include `monitor_backend`, `energy_scope`, `energy_source`, and `energy_confidence` so local-dev, Linux NVIDIA, Windows NVIDIA, and future backends can be distinguished without changing metric formulas.

Energy confidence metadata is optional for backward compatibility with earlier result packages. New runner output should include it to describe sample count, measured duration, minimum recommendations, and warning codes.

Backend ingestion requirements, privacy checks, extracted summary fields, warning codes, and response shapes are defined in `docs/result-ingestion-contract.md`.

The public-safe comparison read model for the future Observatory is defined in `docs/observatory-data-shape.md`.

## Privacy Boundary

Schemas intentionally exclude prompt text, response text, filenames, environment variables, API keys, tokens, and passwords. Implementations should use identifiers for tasks and requests rather than storing private content.

Machine identifiers must be user-chosen labels such as `linux-laptop` or `windows-5070`, not automatically collected hostnames or device serial numbers.

The Evaluation Runner and Telperia Agent use different output contracts. The runner creates complete controlled benchmark result packages. The agent records normal-use inference event, hardware, and environment metadata and must not calculate benchmark scores or capture prompt and response content.

Agent snapshot JSONL records wrap schema-valid payloads with a local `record_type` field:

- `inference_event` wraps `schemas/inference-event.schema.json`.
- `hardware_sample` wraps `schemas/telemetry-sample.schema.json`.
- `environment` records non-private environment metadata such as operating system, GPU model when available, driver version when available, CUDA version when available, inference engine, runtime version, and quantization.

## Versioning

The first schema version is `0.1`. Future incompatible changes should add a new schema version instead of silently changing the meaning of existing result packages.
