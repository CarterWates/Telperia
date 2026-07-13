# Local IPW v0.1

## Status

Approved for MVP implementation as Local IPW v0.1.

## Purpose

Local IPW measures capability delivered per watt-hour for a completed evaluation run on the hardware that actually performs inference.

It is valid for local model execution, such as Ollama running on a measured NVIDIA system. It is not valid for hosted API calls unless the energy measurement comes from the provider-side inference hardware.

## Formula

```text
IPW = TCI * Completion Ratio / GPU Energy in Wh
Displayed IPW = 1000 * TCI * Completion Ratio / GPU Energy in Wh
```

## Implementation Rule

Always preserve the unscaled IPW result. If a scaled display score is shown, store or expose it separately from the unscaled value.

GPU energy must be calculated from raw power samples and preserved with those samples for verification.

Result packages must identify the energy scope and source. For the current runner:

- `energy_scope`: `local_inference_hardware`
- `energy_source`: `local_gpu_telemetry` when GPU energy is measured through NVML
- `energy_source`: `unavailable` when local GPU energy is unavailable

Client-device power must not be used as a proxy for remote data-center inference energy.

## Hosted IPW

Hosted or data-center IPW is deferred. A future methodology may support provider-reported, estimated, or audited data-center energy, but those values must be labeled separately from Local IPW.
