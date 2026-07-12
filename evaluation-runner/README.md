# Evaluation Runner

This directory contains the local Telperia evaluation runner and telemetry code.

## Evaluation Runner

The Phase 4 runner supports Ollama and one model at a time.

Example:

```bash
python3 evaluate.py \
  --model llama3.1:8b \
  --suite suites/tci-v0.1.json \
  --hardware-monitor disabled \
  --output results/run-001.json
```

Use `--hardware-monitor nvml` on supported Linux NVIDIA systems to collect GPU telemetry during the run. Use `disabled` for local development on machines without NVML.

The runner stores task identifiers, scores, latency, token counts, errors, hardware metadata, energy metadata, methodology metadata, and verification metadata. It does not store private prompt or response content in the result package.

## Telemetry Prototype

The Phase 3 telemetry prototype collects local NVIDIA GPU telemetry and exports raw samples without uploading data.

Supported platform:

- Linux.
- NVIDIA GPU.
- NVML available through the NVIDIA driver.
- One local machine.

Example:

```bash
python3 telemetry.py --duration 60 --output telemetry.json
```

Use a `.csv` output path for CSV export:

```bash
python3 telemetry.py --duration 60 --output telemetry.csv
```

On unsupported machines, including Macs without NVML, the command exits with a clear unavailable-telemetry message. That is expected until a separate macOS telemetry collector exists.

The telemetry prototype does not require an account, does not upload data, and does not collect prompt or response content.
