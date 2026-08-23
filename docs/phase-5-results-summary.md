# Phase 5 Results Summary

## Status

These are preliminary Phase 5 seed results. They are useful for validating Telperia result packages, Local IPW calculation, and early Observatory data shape. They should not be presented as a public leaderboard or broad model ranking yet.

## Current Result Packages

| Model | Node | Hardware | TCI | Local IPW | GPU Energy Wh | Samples | Result |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `llama3.1:8b` | `local` | unavailable | 50.0 | deferred | 0 | 0 | `2026-07-12_llama3-1-8b_tci-v0-1_local-dev_001.json` |
| `gemma2:9b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 51.0 | 190.82 | 0.2673 | 28 | `2026-08-23_gemma2-9b_tci-v0-1_windows-nvml_001.json` |
| `gemma2:9b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 56.0 | 331.37 | 0.1690 | 7 | `2026-08-23_gemma2-9b_tci-v0-1_windows-nvml_002.json` |
| `gemma2:9b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 56.0 | 502.96 | 0.1113 | 4 | `2026-08-23_gemma2-9b_tci-v0-1_windows-nvml_003.json` |
| `llama3.1:8b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 45.0 | 239.51 | 0.1879 | 7 | `2026-08-23_llama3-1-8b_tci-v0-1_windows-nvml_001.json` |
| `llama3.1:8b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 45.0 | 248.37 | 0.1812 | 8 | `2026-08-23_llama3-1-8b_tci-v0-1_windows-nvml_002.json` |
| `llama3.1:8b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 37.0 | 235.85 | 0.1569 | 5 | `2026-08-23_llama3-1-8b_tci-v0-1_windows-nvml_003.json` |
| `llama3.2:3b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 31.0 | 418.62 | 0.0741 | 4 | `2026-08-23_llama3-2-3b_tci-v0-1_windows-nvml_001.json` |
| `mistral:7b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 25.0 | 69.17 | 0.3614 | 9 | `2026-08-23_mistral-7b_tci-v0-1_windows-nvml_001.json` |
| `qwen2.5:7b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 50.0 | 363.65 | 0.1375 | 15 | `2026-08-23_qwen2-5-7b_tci-v0-1_windows-nvml_001.json` |
| `qwen2.5:7b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 50.0 | 396.38 | 0.1261 | 7 | `2026-08-23_qwen2-5-7b_tci-v0-1_windows-nvml_002.json` |
| `qwen2.5:7b` | `windows-5070` | NVIDIA GeForce RTX 5070 | 50.0 | 502.42 | 0.0995 | 3 | `2026-08-23_qwen2-5-7b_tci-v0-1_windows-nvml_003.json` |

## Interpretation Notes

- Local IPW is only calculated for result packages with measured local GPU energy.
- Current measured energy values are gross local GPU energy during the evaluation window, not perfectly isolated model-only energy.
- New result packages include energy confidence metadata. Earlier seed result packages remain valid but may not include that field.
- The Mac/local development result is valid for runner and schema validation, but it is not comparable energy evidence.
- The Windows RTX 5070 results are useful for same-hardware comparison across local Ollama models.
- Verification level is currently `0`; future Telperia Verified claims require a stronger approved process.
- The `tci-v0.1` suite is an MVP calibration suite and should be expanded before public model rankings.
- Exact score and telemetry values are preserved in the result JSON files.

## Next Data Priorities

1. Add a Linux NVIDIA/NVML result from a second machine when available.
2. Continue repeat Windows runs to better estimate run-to-run variance.
3. Feed approved summaries into the Phase 6 backend ingestion flow.
4. Keep hosted or data-center IPW separate from Local IPW.
