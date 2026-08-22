# Schemas

Telperia schemas define the portable data contracts used by the runner, telemetry sampler, agent, backend, and public Observatory.

## Files

- `schemas/evaluation-run.schema.json` describes one complete local evaluation result package.
- `schemas/telemetry-sample.schema.json` describes one non-content hardware telemetry sample.
- `schemas/inference-event.schema.json` describes one non-content inference event.

Evaluation run packages may include `run_environment` metadata with a user-chosen `node_id`, operating system family, and monitor backend. Energy blocks may include `monitor_backend`, `energy_scope`, and `energy_source` so local-dev, Linux NVIDIA, Windows NVIDIA, and future backends can be distinguished without changing metric formulas.

## Privacy Boundary

Schemas intentionally exclude prompt text, response text, filenames, environment variables, API keys, tokens, and passwords. Implementations should use identifiers for tasks and requests rather than storing private content.

Machine identifiers must be user-chosen labels such as `linux-laptop` or `windows-5070`, not automatically collected hostnames or device serial numbers.

## Versioning

The first schema version is `0.1`. Future incompatible changes should add a new schema version instead of silently changing the meaning of existing result packages.
