# Evaluation Runner

This directory contains the local Telperia evaluation runner and telemetry code.

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
