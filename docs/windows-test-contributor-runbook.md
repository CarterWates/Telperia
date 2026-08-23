# Windows Test Contributor Runbook

## Status

Phase 5 and Phase 6 contributor runbook for Windows NVIDIA machines. This is written for repeatable local model testing without filling the repository with accidental machine-specific data.

## Goal

Run Telperia evaluations on a Windows NVIDIA machine, validate the result packages, and push a clean branch for review.

## Before You Start

Use this workflow when:

- The machine has an NVIDIA GPU.
- Ollama can run local models.
- There is enough disk space for the selected models.
- The contributor can push a branch to the Telperia repository.

Do not commit prompt text or response text. Do not commit `.env` files, local usernames, hostnames, serial numbers, screenshots of secrets, or unrelated local files.

## Install Tools

Install:

- Git for Windows.
- Python 3.11 or newer.
- Ollama for Windows.
- Current NVIDIA drivers.

Confirm the basics:

```powershell
git --version
python --version
ollama --version
nvidia-smi
```

## Clone The Repo

```powershell
git clone https://github.com/CarterWates/Telperia.git
cd Telperia
git status
```

Expected state:

```text
On branch main
nothing to commit, working tree clean
```

## Run Baseline Tests

```powershell
python -m unittest discover -s tests -q
python -m compileall -q evaluation-runner tests
python evaluation-runner\evaluate.py --help
python evaluation-runner\telemetry.py --help
```

Stop if tests fail before any model run.

## Choose Models Carefully

Start with models that fit comfortably on disk and GPU memory. Good first choices:

```powershell
ollama pull llama3.2:3b
ollama pull qwen2.5:7b
ollama pull mistral:7b
ollama pull gemma2:9b
```

Skip a model if disk space, VRAM, or runtime looks risky. Smaller clean runs are more useful than an unstable batch.

## Create A Results Branch

Use a branch name that says what machine and run batch produced the results:

```powershell
git checkout -b phase-5-windows-5070-results
```

If the branch already exists locally, use a new suffix:

```powershell
git checkout -b phase-5-windows-5070-results-002
```

## Run An Evaluation

Example:

```powershell
python evaluation-runner/evaluate.py --model qwen2.5:7b --output datasets/results/2026-08-23_qwen2-5-7b_tci-v0-1_windows-nvml_004.json --hardware-monitor nvml --node-id windows-5070
```

Use:

- `--hardware-monitor nvml` on Windows NVIDIA machines.
- `--node-id windows-5070` or another simple user-chosen label.
- A unique output filename for every run.

Do not reuse an existing result filename unless intentionally replacing a rejected local file before commit.

## Repeatability

For stronger energy confidence and model comparison:

- Run at least two repeats per model when time allows.
- Keep background apps quiet.
- Do not run games, rendering workloads, or other GPU-heavy tasks during evaluation.
- Record skipped models in the final report if a model cannot fit or run cleanly.

## Validate Results

After every batch:

```powershell
python -m unittest discover -s tests -q
```

Then run a local validation summary:

```powershell
python - <<'PY'
import json
import sys
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str(root / "evaluation-runner"))
from telperia_runner.ingestion import validate_ingestion_package

schema = root / "schemas" / "evaluation-run.schema.json"
for path in sorted((root / "datasets" / "results").glob("*.json")):
    result = validate_ingestion_package(json.loads(path.read_text()), schema)
    print(path.name, result.accepted, result.error_code, result.validation_warnings)
PY
```

Expected:

- New valid Windows NVIDIA results are accepted.
- Local IPW is calculated when GPU energy is positive.
- Low energy confidence may warn on short runs.
- `error_count` should usually be `0`.

## Review The Diff

```powershell
git status
git diff --stat
```

Expected files:

- New JSON files under `datasets/results/`.
- Optional dataset README updates if the run table is updated.

Unexpected files to remove before commit:

- `.env`
- logs containing secrets
- screenshots
- cache folders
- downloaded model files
- unrelated editor files

## Commit And Push

```powershell
git add datasets/results
git commit -m "data: add windows nvidia evaluation results"
git push origin HEAD
```

If docs were updated too:

```powershell
git add datasets/results docs
git commit -m "data: add windows nvidia evaluation results"
git push origin HEAD
```

## Final Report Template

Include this in the Codex desktop task or pull request notes:

```text
Branch:
Commit:
Models tested:
Runs per model:
Skipped models:
Disk free before:
Disk free after:
Validation:
- Unit tests:
- Result schema validation:
- Ingestion validation:
- Secret scan:
Notes:
```

## Stop Conditions

Stop and ask before pushing if:

- A result package contains prompt or response text.
- A result package fails schema or ingestion validation.
- GPU energy is negative, missing, or obviously impossible.
- The repo has unrelated code changes.
- Any secret-like value appears in the diff.
- A model causes repeated system instability.
