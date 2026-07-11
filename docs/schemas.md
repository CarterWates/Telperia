# Schemas

Telperia schemas define the portable data contracts used by the runner, telemetry sampler, agent, backend, and public Observatory.

## Files

- `schemas/evaluation-run.schema.json` describes one complete local evaluation result package.
- `schemas/telemetry-sample.schema.json` describes one non-content hardware telemetry sample.
- `schemas/inference-event.schema.json` describes one non-content inference event.

## Privacy Boundary

Schemas intentionally exclude prompt text, response text, filenames, environment variables, API keys, tokens, and passwords. Implementations should use identifiers for tasks and requests rather than storing private content.

## Versioning

The first schema version is `0.1`. Future incompatible changes should add a new schema version instead of silently changing the meaning of existing result packages.
