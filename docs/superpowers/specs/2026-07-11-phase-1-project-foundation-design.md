# Phase 1 Project Foundation Design

## Purpose

Phase 1 establishes the Telperia repository foundation without implementing runtime behavior. It creates the project structure, repository guidance, methodology document locations, and basic roadmap documentation needed for later phases.

This phase deliberately avoids telemetry, scoring formulas, backend ingestion, web UI implementation, dependency installation, and evaluation runner code.

## Scope

Phase 1 will create:

- A Git-backed repository in `/Users/carter/Desktop/Observatory`.
- Top-level directories matching the Telperia MVP roadmap.
- `AGENTS.md` with Telperia-specific Codex instructions.
- Versioned methodology starter documents in `methodology/`.
- A project `README.md` describing the MVP objective and phase order.
- `docs/roadmap.md` summarizing the planned phases and MVP completion criteria.

Phase 1 will not create:

- Python packages, Node packages, or dependency lockfiles.
- Telemetry sampler code.
- Evaluation runner code.
- API/backend code.
- Web application code.
- Scoring formula implementations.
- Dataset contents.
- Upload, authentication, or cloud behavior.

## Repository Structure

The repository will use the roadmap's suggested structure:

```text
telperia/
├── apps/
│   ├── observatory-web/
│   └── api/
├── agent/
├── evaluation-runner/
├── methodology/
├── schemas/
├── datasets/
├── scripts/
├── tests/
└── docs/
```

Because the workspace directory is already named `Observatory`, the repository root itself will represent `telperia/`; no nested `telperia/` directory will be created unless the user explicitly requests it later.

## Methodology Documents

Phase 1 will create the roadmap's methodology files:

- `methodology/TCI-v0.1.md`
- `methodology/TRI-v0.1.md`
- `methodology/IPW-v0.1.md`
- `methodology/factual-reliability-v0.1.md`
- `methodology/transparency-score-v0.1.md`
- `methodology/bias-evaluation-v0.1.md`
- `methodology/verification-levels.md`
- `methodology/privacy-policy.md`
- `methodology/limitations.md`

These files will be starter documents, not invented methodology. Where the roadmap does not provide full formulas or source text, the documents will clearly say that the authoritative methodology text must be supplied or approved before implementation.

The one exception is `methodology/IPW-v0.1.md`, which may include the formula explicitly provided in the roadmap:

```text
IPW = TCI * Completion Ratio / GPU Energy in Wh
Displayed IPW = 1000 * TCI * Completion Ratio / GPU Energy in Wh
```

No other formulas will be invented.

## AGENTS.md

`AGENTS.md` will include the Telperia Codex rules from the roadmap:

- Read relevant methodology and schema files before implementing a feature.
- Never invent or change metric formulas without explicit approval.
- Keep raw measurements separate from calculated scores.
- Never hard-code secrets, tokens, passwords, or API keys.
- Add tests for calculation and validation logic.
- Preserve backward compatibility with existing schema versions.
- Do not collect prompts or model responses by default.
- Ensure all public results contain methodology and verification metadata.
- Prefer small, reviewable changes over large refactors.
- Explain every modified file after completing a task.
- Do not modify unrelated files.

It will also clarify that Phase 1 files are scaffolding and that future implementation must follow the phase order unless the user says otherwise.

## Documentation

`README.md` will introduce Telperia as an MVP for transparent measurements of local AI model capability, reliability, efficiency, and verification metadata. It will identify the primary MVP components:

- Observatory website.
- Evaluation runner.
- Hardware telemetry sampler.
- Lightweight telemetry agent.
- Backend ingestion layer.

`docs/roadmap.md` will preserve the phase order and MVP completion definition in a concise project-owned form. It will avoid adding commitments not present in the roadmap.

## Testing And Verification

Phase 1 is documentation and structure only, so there are no runtime unit tests. Verification will consist of:

- Confirming expected directories exist.
- Confirming expected files exist.
- Confirming no runtime/package dependency files were introduced.
- Confirming git status shows only the intended Phase 1 files after implementation.

Later phases will introduce tests when calculation, schema validation, telemetry, and runner behavior are implemented.

## Open Decisions Deferred To Later Phases

The following decisions are intentionally deferred:

- Python package layout for telemetry and runner code.
- FastAPI project structure and database layer.
- Supabase versus local PostgreSQL setup.
- Frontend framework and hosting workflow.
- JSON Schema details beyond file placement.
- Dataset format and benchmark prompt content.
- Public submission validation rules beyond roadmap language.

## Success Criteria

Phase 1 is complete when:

- The repository has the agreed top-level structure.
- `AGENTS.md` exists with Telperia-specific guidance.
- The methodology document set exists and does not invent unapproved formulas.
- `README.md` and `docs/roadmap.md` describe the MVP direction and phase order.
- The work is committed as a small, reviewable foundation change.
