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
