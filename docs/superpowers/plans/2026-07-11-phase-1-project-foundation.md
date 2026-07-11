# Phase 1 Project Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the Telperia repository foundation with the agreed directory structure, Codex guidance, methodology starter documents, and project roadmap docs.

**Architecture:** Phase 1 is a documentation and scaffolding layer only. The repository root at `/Users/carter/Desktop/Observatory` represents the Telperia project root, with empty component directories reserved for later phases and Markdown files carrying the initial project rules and phase map.

**Tech Stack:** Git, Markdown, POSIX shell commands for verification. No Python, Node, database, backend, frontend, telemetry, or runtime dependencies are introduced in this phase.

## Global Constraints

- Keep Phase 1 limited to repository structure and documentation.
- Do not create Python packages, Node packages, dependency lockfiles, app code, telemetry code, evaluation runner code, backend code, or web UI code.
- Do not invent or change metric formulas without explicit approval.
- Raw measurements must remain separate from calculated scores in all future implementation guidance.
- Do not collect prompts or model responses by default.
- All public results must contain methodology and verification metadata.
- Preserve backward compatibility with existing schema versions once schemas exist.
- Explain every modified file after completing a task.
- Do not modify unrelated files.

---

## File Structure

Create or modify these files and directories:

- Create directory: `apps/`
- Create directory: `apps/observatory-web/`
- Create directory: `apps/api/`
- Create directory: `agent/`
- Create directory: `evaluation-runner/`
- Create directory: `methodology/`
- Create directory: `schemas/`
- Create directory: `datasets/`
- Create directory: `scripts/`
- Create directory: `tests/`
- Create file: `.gitkeep` inside each empty top-level implementation directory so Git tracks the structure.
- Create file: `AGENTS.md`
- Create file: `README.md`
- Create file: `docs/roadmap.md`
- Create file: `methodology/TCI-v0.1.md`
- Create file: `methodology/TRI-v0.1.md`
- Create file: `methodology/IPW-v0.1.md`
- Create file: `methodology/factual-reliability-v0.1.md`
- Create file: `methodology/transparency-score-v0.1.md`
- Create file: `methodology/bias-evaluation-v0.1.md`
- Create file: `methodology/verification-levels.md`
- Create file: `methodology/privacy-policy.md`
- Create file: `methodology/limitations.md`

---

### Task 1: Track The Repository Skeleton

**Files:**
- Create: `apps/observatory-web/.gitkeep`
- Create: `apps/api/.gitkeep`
- Create: `agent/.gitkeep`
- Create: `evaluation-runner/.gitkeep`
- Create: `methodology/.gitkeep`
- Create: `schemas/.gitkeep`
- Create: `datasets/.gitkeep`
- Create: `scripts/.gitkeep`
- Create: `tests/.gitkeep`

**Interfaces:**
- Consumes: No prior task output.
- Produces: Git-tracked directories for later phases:
  - `apps/observatory-web/` for the public Observatory website.
  - `apps/api/` for backend ingestion and API code.
  - `agent/` for the continuous Telperia Agent.
  - `evaluation-runner/` for controlled benchmark execution.
  - `methodology/` for versioned metric and privacy documentation.
  - `schemas/` for JSON Schemas beginning in Phase 2.
  - `datasets/` for benchmark and seed result data.
  - `scripts/` for repo utilities.
  - `tests/` for shared tests.

- [ ] **Step 1: Create tracked directories**

Run:

```bash
mkdir -p apps/observatory-web apps/api agent evaluation-runner methodology schemas datasets scripts tests
touch apps/observatory-web/.gitkeep apps/api/.gitkeep agent/.gitkeep evaluation-runner/.gitkeep methodology/.gitkeep schemas/.gitkeep datasets/.gitkeep scripts/.gitkeep tests/.gitkeep
```

Expected: command exits successfully with no output.

- [ ] **Step 2: Verify the skeleton exists**

Run:

```bash
find apps agent evaluation-runner methodology schemas datasets scripts tests -maxdepth 2 -type f | sort
```

Expected output:

```text
agent/.gitkeep
apps/api/.gitkeep
apps/observatory-web/.gitkeep
datasets/.gitkeep
evaluation-runner/.gitkeep
methodology/.gitkeep
schemas/.gitkeep
scripts/.gitkeep
tests/.gitkeep
```

- [ ] **Step 3: Commit the skeleton**

Run:

```bash
git add apps agent evaluation-runner methodology schemas datasets scripts tests
git commit -m "chore: add telperia repository skeleton"
```

Expected: commit succeeds and includes only `.gitkeep` files.

---

### Task 2: Add Telperia Codex Guidance

**Files:**
- Create: `AGENTS.md`

**Interfaces:**
- Consumes: Directory structure from Task 1.
- Produces: Repository-level instructions future Codex work must read before implementation.

- [ ] **Step 1: Create `AGENTS.md`**

Add this exact content:

```markdown
# Telperia Codex Instructions

These instructions apply to all work in this repository.

## Project Order

- Work through the Telperia MVP phases in order unless the user explicitly changes priority.
- Keep each phase small, reviewable, and independently verifiable.
- Do not modify unrelated files.
- Explain every created or modified file after completing a task.

## Methodology And Scoring

- Read the relevant methodology and schema files before implementing a feature.
- Never invent or change metric formulas without explicit approval.
- Raw measurements must remain separate from calculated scores.
- Preserve unscaled scores when a scaled display score is also shown.
- Preserve backward compatibility with existing schema versions.
- All public results must contain methodology and verification metadata.

## Privacy And Data Collection

- Do not collect prompts or model responses by default.
- Do not collect filenames, environment variables, API keys, tokens, or passwords.
- Never hard-code secrets, tokens, passwords, or API keys.
- Uploaded data must remain private unless the user explicitly chooses public submission.
- Research contribution behavior must be explicit opt-in.

## Testing And Validation

- Add tests for all calculation and validation logic.
- Validate result packages against the relevant schema before accepting or publishing them.
- Reject impossible measurements such as negative energy values or invalid percentages.
- Prefer clear, deterministic tests over broad snapshots.

## Engineering Style

- Prefer small, reviewable changes over large refactors.
- Follow existing local patterns once code exists.
- Use structured parsers and validators for structured data.
- Keep runtime code, schemas, methodology, and raw data in separate files.
```

- [ ] **Step 2: Verify the guidance is present**

Run:

```bash
sed -n '1,220p' AGENTS.md
```

Expected: the output matches the content from Step 1.

- [ ] **Step 3: Commit the guidance**

Run:

```bash
git add AGENTS.md
git commit -m "docs: add telperia agent instructions"
```

Expected: commit succeeds and includes only `AGENTS.md`.

---

### Task 3: Add Methodology Starter Documents

**Files:**
- Create: `methodology/TCI-v0.1.md`
- Create: `methodology/TRI-v0.1.md`
- Create: `methodology/IPW-v0.1.md`
- Create: `methodology/factual-reliability-v0.1.md`
- Create: `methodology/transparency-score-v0.1.md`
- Create: `methodology/bias-evaluation-v0.1.md`
- Create: `methodology/verification-levels.md`
- Create: `methodology/privacy-policy.md`
- Create: `methodology/limitations.md`
- Modify: remove `methodology/.gitkeep` after real files exist.

**Interfaces:**
- Consumes: `methodology/` directory from Task 1 and methodology constraints from `AGENTS.md`.
- Produces: Versioned methodology document locations that later schema, scoring, runner, backend, and UI work can reference.

- [ ] **Step 1: Create `methodology/TCI-v0.1.md`**

Add this exact content:

```markdown
# TCI v0.1

## Status

Draft scaffold. The authoritative TCI v0.1 methodology text and formula weights must be supplied or explicitly approved before implementation.

## Purpose

TCI is intended to measure model capability across the evaluation categories defined for the Telperia MVP, including reasoning, coding, mathematics, factual knowledge, and instruction adherence.

## Implementation Rule

Do not implement TCI calculations from this scaffold alone. Future implementation must preserve raw benchmark scores, normalized benchmark scores, category scores, category weights, and the final TCI score separately.
```

- [ ] **Step 2: Create `methodology/TRI-v0.1.md`**

Add this exact content:

```markdown
# TRI v0.1

## Status

Draft scaffold. The authoritative TRI v0.1 methodology text and formulas must be supplied or explicitly approved before implementation.

## Purpose

TRI is reserved for Telperia reliability methodology. The MVP roadmap requires the website to explain what TRI measures, but it does not provide an implementation formula in Phase 1.

## Implementation Rule

Do not implement TRI calculations from this scaffold alone.
```

- [ ] **Step 3: Create `methodology/IPW-v0.1.md`**

Add this exact content:

````markdown
# IPW v0.1

## Status

Draft scaffold with the formulas provided in the Telperia MVP roadmap.

## Purpose

IPW measures capability delivered per watt-hour for a completed evaluation run on specific hardware.

## Formula

```text
IPW = TCI * Completion Ratio / GPU Energy in Wh
Displayed IPW = 1000 * TCI * Completion Ratio / GPU Energy in Wh
```

## Implementation Rule

Always preserve the unscaled IPW result. If a scaled display score is shown, store or expose it separately from the unscaled value.

GPU energy must be calculated from raw power samples and preserved with those samples for verification.
````

- [ ] **Step 4: Create `methodology/factual-reliability-v0.1.md`**

Add this exact content:

```markdown
# Factual Reliability v0.1

## Status

Draft scaffold. The authoritative factual reliability methodology text must be supplied or explicitly approved before implementation.

## Purpose

Factual Reliability is intended to measure correctness, incorrect responses, abstentions, and attempted accuracy for factual evaluation tasks.

## Required Raw Values

Future implementations must preserve:

- Correct responses.
- Incorrect responses.
- Abstentions.
- Total questions.
- Correctness rate.
- Incorrect answer rate.
- Abstention rate.
- Attempted accuracy.
```

- [ ] **Step 5: Create `methodology/transparency-score-v0.1.md`**

Add this exact content:

```markdown
# Transparency Score v0.1

## Status

Draft scaffold. The authoritative transparency score methodology must be supplied or explicitly approved before implementation.

## Purpose

The Transparency Score is intended to describe the evidence available for model, evaluation, hardware, methodology, and verification claims.

## Implementation Rule

Do not implement transparency scoring from this scaffold alone. Public results must link displayed transparency values to their methodology version and evidence.
```

- [ ] **Step 6: Create `methodology/bias-evaluation-v0.1.md`**

Add this exact content:

```markdown
# Bias Evaluation v0.1

## Status

Draft scaffold. The authoritative bias evaluation methodology must be supplied or explicitly approved before implementation.

## Purpose

Bias evaluation is reserved for future Telperia methodology work and should not be treated as complete in the MVP foundation.

## Implementation Rule

Do not implement bias evaluation scoring from this scaffold alone.
```

- [ ] **Step 7: Create `methodology/verification-levels.md`**

Add this exact content:

```markdown
# Verification Levels

## Status

Draft scaffold. The authoritative verification level definitions must be supplied or explicitly approved before implementation.

## Purpose

Verification levels describe the evidence and trust level behind a result. Every public score must include a verification level.

## MVP Rule

Community submissions may be labeled `Community Measured`. They must not be described as tamper-proof or Telperia Verified unless a later approved verification process supports that claim.
```

- [ ] **Step 8: Create `methodology/privacy-policy.md`**

Add this exact content:

```markdown
# Privacy Policy

## Status

Draft scaffold for MVP engineering constraints. This is not legal advice or a final public privacy policy.

## MVP Data Collection Rules

- Do not collect prompts by default.
- Do not collect model responses by default.
- Do not collect filenames, environment variables, API keys, tokens, or passwords.
- Local evaluation must run without requiring an account or network connection.
- Uploaded results must remain private unless the user explicitly chooses public submission.
- Research Contribution Mode must be disabled by default.
```

- [ ] **Step 9: Create `methodology/limitations.md`**

Add this exact content:

```markdown
# Known Limitations

## Status

Draft scaffold.

## MVP Limitations

The MVP intentionally does not include:

- Native iOS application.
- Enterprise billing.
- Team workspaces.
- Kubernetes integration.
- AMD support.
- Apple Silicon support.
- Distributed inference.
- Prompt collection.
- Response collection.
- Automatic hallucination analysis of private conversations.
- Carbon claims without reliable methodology.
- One universal model ranking.
- Autonomous model optimization.
- Proprietary hardware.
- Complex AI recommendations.
- Mobile push notifications.
```

- [ ] **Step 10: Remove the methodology tracking file**

Run:

```bash
git rm methodology/.gitkeep
```

Expected: `methodology/.gitkeep` is staged for deletion because real methodology files now track the directory.

- [ ] **Step 11: Verify methodology files**

Run:

```bash
find methodology -maxdepth 1 -type f | sort
```

Expected output:

```text
methodology/IPW-v0.1.md
methodology/TCI-v0.1.md
methodology/TRI-v0.1.md
methodology/bias-evaluation-v0.1.md
methodology/factual-reliability-v0.1.md
methodology/limitations.md
methodology/privacy-policy.md
methodology/transparency-score-v0.1.md
methodology/verification-levels.md
```

- [ ] **Step 12: Commit methodology starters**

Run:

```bash
git add methodology
git commit -m "docs: add methodology v0.1 starters"
```

Expected: commit succeeds and includes the nine methodology files plus removal of `methodology/.gitkeep`.

---

### Task 4: Add Project README, Roadmap, And Verification

**Files:**
- Create: `README.md`
- Create: `docs/roadmap.md`

**Interfaces:**
- Consumes: Directory skeleton from Task 1, `AGENTS.md` from Task 2, methodology files from Task 3.
- Produces: Human-readable project orientation and phase map for future implementation.

- [ ] **Step 1: Create `README.md`**

Add this exact content:

```markdown
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

Phase 1 creates the project foundation only. Runtime implementation starts in later phases.
```

- [ ] **Step 2: Create `docs/roadmap.md`**

Add this exact content:

```markdown
# Telperia MVP Roadmap

## Phase Order

1. Create the project foundation.
2. Define the data schemas.
3. Build the hardware telemetry prototype.
4. Build the evaluation runner.
5. Run initial local experiments.
6. Build the backend.
7. Build the Observatory website.
8. Build the Telperia Agent.
9. Build the personal node dashboard.
10. Add community submissions.
11. Seed the public Observatory.
12. Improve the platform.

## MVP Completion Definition

The Telperia MVP is complete when:

- The methodology is publicly documented.
- At least five model configurations have published results.
- Every score includes a methodology version.
- Every score includes a verification level.
- Every IPW result includes hardware and energy data.
- The evaluation runner works on a supported NVIDIA system.
- Users can generate a valid result package.
- Users can upload a result privately or publicly.
- The agent can collect non-content telemetry.
- Public model profiles can be compared.
- Raw measurements remain available for verification.
- Privacy modes are clear and functional.
- The platform clearly states its limitations.

## Phase 1 Boundary

Phase 1 creates repository structure and documentation only. It does not introduce app code, telemetry code, runner code, backend code, schema definitions, package dependencies, or scoring implementations.
```

- [ ] **Step 3: Verify no runtime package files were added**

Run:

```bash
find . -maxdepth 3 \( -name package.json -o -name package-lock.json -o -name pyproject.toml -o -name requirements.txt -o -name poetry.lock -o -name uv.lock \) -print
```

Expected: no output.

- [ ] **Step 4: Verify required Phase 1 files exist**

Run:

```bash
test -f AGENTS.md
test -f README.md
test -f docs/roadmap.md
test -f methodology/TCI-v0.1.md
test -f methodology/TRI-v0.1.md
test -f methodology/IPW-v0.1.md
test -f methodology/factual-reliability-v0.1.md
test -f methodology/transparency-score-v0.1.md
test -f methodology/bias-evaluation-v0.1.md
test -f methodology/verification-levels.md
test -f methodology/privacy-policy.md
test -f methodology/limitations.md
```

Expected: command exits successfully with no output.

- [ ] **Step 5: Review the pending file set**

Run:

```bash
git status --short
```

Expected: only `README.md` and `docs/roadmap.md` are uncommitted at this point.

- [ ] **Step 6: Commit project docs**

Run:

```bash
git add README.md docs/roadmap.md
git commit -m "docs: add project overview and roadmap"
```

Expected: commit succeeds and includes only `README.md` and `docs/roadmap.md`.

- [ ] **Step 7: Run final Phase 1 verification**

Run:

```bash
find apps agent evaluation-runner methodology schemas datasets scripts tests -maxdepth 2 -print | sort
git status --short
```

Expected: the directory tree includes the Phase 1 directories and files, and `git status --short` has no output.

- [ ] **Step 8: Prepare completion summary**

Report the created files grouped by purpose:

- Repository skeleton: `.gitkeep` files for empty future implementation directories.
- Agent guidance: `AGENTS.md`.
- Methodology starters: nine files in `methodology/`.
- Project docs: `README.md` and `docs/roadmap.md`.

Also report that no runtime dependencies, app code, telemetry code, runner code, backend code, or scoring implementations were added.
