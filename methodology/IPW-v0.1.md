# Local IPW v0.1

## Status

Approved for MVP implementation as Local IPW v0.1.

## Purpose

Local IPW measures capability delivered per watt-hour for a completed evaluation run on the hardware that actually performs inference.

It is valid for local model execution, such as Ollama running on a measured Linux or Windows NVIDIA system. It is not valid for hosted API calls unless the energy measurement comes from the provider-side inference hardware.

## Formula

```text
IPW = TCI * Completion Ratio / GPU Energy in Wh
Displayed IPW = 1000 * TCI * Completion Ratio / GPU Energy in Wh
```

## Implementation Rule

Always preserve the unscaled IPW result. If a scaled display score is shown, store or expose it separately from the unscaled value.

GPU energy must be calculated from raw power samples and preserved with those samples for verification.

Local IPW v0.1 uses gross measured GPU energy during the evaluation window. This includes all GPU power draw observed during the run, so background GPU activity can influence the value. It should not be described as perfectly isolated model-only energy unless a stricter isolation and baseline process is used.

Result packages must identify the energy scope and source. For the current runner:

- `energy_scope`: `local_inference_hardware`
- `energy_source`: `local_gpu_telemetry` when GPU energy is measured through NVML
- `energy_source`: `unavailable` when local GPU energy is unavailable

Result packages should also identify the monitor backend. For the current runner:

- `monitor_backend`: `nvml` when Linux or Windows NVIDIA telemetry is collected through NVML
- `monitor_backend`: `disabled` for Mac local-development runs or other machines without approved local energy telemetry

Result packages should include energy confidence metadata when available. Energy confidence does not change the IPW formula. It describes the quality of the energy measurement behind the score.

For the current runner:

- `quality`: `unavailable` when local GPU energy is not measured.
- `quality`: `low` when a measured run has fewer than 10 power samples or less than 30 seconds of measured duration.
- `quality`: `medium` when a measured run meets the minimum sample and duration thresholds.
- `warning_codes`: machine-readable notes such as `energy_unavailable`, `low_sample_count`, `short_duration`, and `gross_energy_scope`.

The MVP runner does not assign `high` energy confidence. A future methodology may reserve high confidence for repeated runs, idle-baseline adjustment, or stronger isolation controls.

Client-device power must not be used as a proxy for remote data-center inference energy.

Mac local-development runs may calculate TCI and Factual Reliability, but Local IPW must remain deferred until a separate Apple hardware energy methodology is approved.

## Repeatability Protocol

For Phase 5 MVP evidence, measured NVIDIA runs should follow a repeatable setup:

1. Close GPU-heavy applications before the run.
2. Keep the machine plugged in and use the same operating system power mode.
3. Let the GPU idle briefly before starting the evaluation.
4. Avoid games, video rendering, screen recording, other local AI tools, or CUDA workloads during the run.
5. Record the result as gross local GPU energy unless an approved baseline-adjusted method is used.
6. Repeat important model/hardware runs two or more times when possible.
7. Preserve every raw result package instead of replacing earlier runs.

Future methodology versions may add idle-baseline measurement and baseline-adjusted Local IPW. If that happens, gross measured GPU energy must still be preserved separately from any adjusted value.

## Hosted IPW

Hosted or data-center IPW is deferred. A future methodology may support provider-reported, estimated, or audited data-center energy, but those values must be labeled separately from Local IPW.
