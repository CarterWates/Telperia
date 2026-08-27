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

## Agent Privacy Modes

- Private Mode is active and default. It writes local JSONL records only and does not upload data.
- Personal Cloud Mode is planned for encrypted metrics in a user's private dashboard. It must remain blocked until backend authentication, encryption, and private storage support exist.
- Research Contribution Mode is planned for selected anonymized aggregate research data. It must require explicit opt-in and must remain disabled by default.

The current MVP has no Agent upload path for any mode.

Local Agent buffering must remain under the user-selected output directory. Users must be able to pause collection, inspect collected fields, and delete Agent-owned local buffer files without deleting unrelated files.
