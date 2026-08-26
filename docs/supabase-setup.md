# Supabase Setup Guide

## Status

Phase 6 preparation guide. These steps are for opening or reactivating the Telperia Supabase project and safely applying the backend migration later. Do not paste secrets into this repository.

The current migration draft is:

```text
supabase/migrations/20260823000000_phase_6_result_ingestion.sql
```

## What Supabase Will Handle

The MVP backend is expected to use:

- Auth for private user uploads.
- Postgres for upload records and public-safe summaries.
- Storage for private raw result package JSON.
- RLS for owner-scoped access and public-approved summaries.
- Advisors and database linting before any production launch.

## Open Or Reactivate The Project

1. Go to the Supabase dashboard.
2. Select the Telperia organization.
3. Open the existing Telperia project if it is active.
4. If the project is paused, open the paused project and choose `Resume project`.
5. Wait until the project status is active before linking the CLI or applying migrations.
6. If the project cannot be resumed, create a new project and keep the old one untouched until backups are reviewed.

Supabase Free Plan projects can pause after low activity. Supabase documents that paused projects can be restored from the dashboard within the restore window, and paid projects are not automatically paused.

## Local Tools

Install before applying migrations:

- Supabase CLI.
- Docker Desktop if running local Supabase.
- A current Git checkout of this repository.

Confirm the CLI works:

```bash
supabase --version
supabase --help
```

If the CLI is missing, install it from the current Supabase CLI docs rather than guessing an old command.

## Environment Variables

Keep secrets in a local `.env`, shell profile, password manager, or hosting dashboard. Do not commit them.

Local CLI variables:

```bash
SUPABASE_PROJECT_REF=your-project-ref
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_ACCESS_TOKEN=your-personal-access-token
```

Frontend/public variables for the future Observatory app:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-publishable-key
```

Server-only variables for future ingestion code:

```bash
TELPERIA_SUPABASE_URL=https://your-project-ref.supabase.co
TELPERIA_SUPABASE_SERVER_KEY=your-server-only-key
```

Rules:

- Never prefix server-only values with `NEXT_PUBLIC_`.
- Never commit `.env` files containing real values.
- Prefer publishable keys for browser code.
- Use server-only credentials only in trusted backend code.

## Link The Project

From the repository root:

```bash
supabase login
supabase link --project-ref "$SUPABASE_PROJECT_REF"
supabase migration list
```

Check that the local and remote migration lists make sense before pushing anything.

## Safe Local Migration Check

If Docker is available, test the migration locally first:

```bash
supabase start
supabase db reset --local
supabase db lint --local --fail-on warning
supabase migration list --local
```

Expected outcome:

- The database starts locally.
- The Phase 6 migration applies.
- Lint has no unresolved warnings.
- The migration list shows the Phase 6 migration locally.

If local reset fails, stop and inspect the first SQL error before changing the migration.

## Safe Remote Migration Flow

Do not push directly to production first.

Recommended order:

1. Apply to a local database.
2. Apply to a Supabase preview branch or staging project.
3. Run advisors and inspect policies.
4. Only then apply to production.

Dry run first:

```bash
supabase db push --dry-run
```

If the dry run is clean and the target project is correct:

```bash
supabase db push
supabase migration list
```

Do not use remote migration repair unless the migration history is already broken and the exact repair has been reviewed.

## Advisors And Security Checks

Run these after the migration is applied to local, staging, or production:

```bash
supabase db lint --local --fail-on warning
supabase db lint --linked --fail-on warning
```

Then open the Supabase dashboard:

1. Go to `Database`.
2. Open `Security Advisor`.
3. Review every finding.
4. Open `Performance Advisor`.
5. Review missing indexes, duplicate indexes, and slow-query suggestions.
6. Confirm RLS is enabled for all public-schema application tables.
7. Confirm the `result-packages` Storage bucket is private.
8. Confirm public clients cannot read private raw result package objects.

Expected Phase 6 checks:

- No public raw JSON bucket.
- No direct public access to private upload rows.
- No user-editable metadata used for authorization.
- No server-only key in frontend variables.
- No broad authenticated write grants to trusted summary tables.
- Public reads expose only approved summary rows.

## Repo Tests To Run

Before and after Supabase work:

```bash
python3 -m unittest discover -s tests -q
python3 -m compileall -q evaluation-runner tests
```

Optional local package validation:

```bash
python3 - <<'PY'
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

## Stop Conditions

Stop before applying remote changes if:

- The target project ref is unclear.
- Supabase CLI asks to repair history unexpectedly.
- The dry run shows migrations you did not expect.
- Advisors report RLS disabled, public bucket access, exposed sensitive columns, or unsafe policies.
- Any real secret appears in git status, diffs, logs, screenshots, or issue text.

## Current Limitation

This repository currently contains a local API wrapper, local SQLite persistence, a Supabase migration foundation, and local validation tests. It does not yet contain live Supabase database client wiring or deployed Supabase project configuration.
