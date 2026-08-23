# Telperia Security Review Checklist

## Purpose

Telperia handles evaluation results, methodology metadata, local hardware summaries, and future user uploads. The project must stay careful about secrets, prompt and response privacy, raw result storage, and public review.

Use this checklist before merging backend, ingestion, dataset, release, or website changes.

## Secrets

- Do not commit `.env` files.
- Do not commit Supabase access tokens, database passwords, server-only keys, API keys, passwords, or private tokens.
- Do not prefix server-only credentials with `NEXT_PUBLIC_`.
- Do not paste secrets into issues, docs, screenshots, result packages, logs, or fixture files.
- Run a secret scan before pushing security-sensitive changes.

## Prompt And Response Privacy

- Do not save prompt text or model response text in result packages by default.
- Do not upload prompt text or response text through ingestion.
- Keep evaluation task IDs, category names, numeric scores, latency, token counts, and telemetry metadata separate from prompt and response content.
- Reject packages containing `prompt`, `response`, `prompt_text`, `response_text`, `content`, `filename`, `file_path`, `environment`, `env`, `hostname`, `serial_number`, `api_key`, `token`, `password`, or `secret` keys.
- Public pages should use extracted summary fields, not raw private files.

## Public Uploads

- New uploads start as `private`.
- `submit_for_public_review` creates a review request, not an automatic public result.
- Direct `public` visibility on first upload must be rejected.
- Public publication requires an accepted upload, owner intent, and review status.
- Public rows must not expose user account IDs, emails, private Storage paths, prompts, responses, filenames, hostnames, serial numbers, or credentials.

## RLS

- Enable RLS on every application table in exposed schemas.
- Revoke broad default grants before granting only required privileges.
- Use explicit `TO anon` and `TO authenticated` clauses.
- Use owner predicates such as `(select auth.uid()) = user_id` for private rows.
- Use both `USING` and `WITH CHECK` on owner-controlled updates.
- Do not rely on user-editable metadata for authorization.
- Avoid `SECURITY DEFINER` functions unless there is a documented reason, an owner check, and a non-exposed schema.
- Run Supabase Security Advisor after migration changes are applied to a real project.

## Private Raw JSON

- Store complete raw result packages in the private `result-packages` bucket.
- Generate Storage paths on the backend.
- Do not trust client-provided Storage paths.
- Keep raw JSON private even when a public summary is approved.
- Public Observatory views should read summary tables, not private raw Storage URLs.

## Dataset Review

- Validate every result package against `schemas/evaluation-run.schema.json`.
- Run the local ingestion validator on every dataset result before publication.
- Reject impossible measurements such as negative energy, invalid percentages, broken completion ratios, or broken Local IPW math.
- Preserve unscaled Local IPW when a scaled display score exists.
- Preserve raw benchmark scores, normalized scores, category scores, and category weights.
- Keep TCI v0.2 proposal data separate from active TCI v0.1 results.

## Release Checklist

Before a release or production migration:

- Run `python3 -m unittest discover -s tests -q`.
- Run `python3 -m compileall -q evaluation-runner tests`.
- Validate dataset results and ingestion fixtures.
- Run a secret scan.
- Review `git status` and `git diff --stat`.
- Confirm no `.env`, cache, screenshots, logs, or model files are staged.
- Confirm Supabase migration dry run output matches expectations.
- Run Supabase Security Advisor and Performance Advisor.
- Confirm the `result-packages` bucket is private.
- Confirm public views expose only approved public summaries.

## Stop Conditions

Stop and review before pushing if:

- A real secret appears anywhere in the diff.
- A result package contains prompt or response content.
- A migration weakens RLS, grants broad writes, or exposes private raw JSON.
- A public row includes private owner, Storage, host, filename, or credential fields.
- Tests or validators fail.
