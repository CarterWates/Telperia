# Observatory Fixtures

`public_rows.json` contains public-safe comparison rows that match `docs/observatory-data-shape.md`.

The rows are derived from accepted seed packages in `datasets/results/` through `extract_observatory_row`, not from private raw Storage objects. They are intended for Phase 7 website and API tests where realistic leaderboard data is useful without exposing prompts, responses, filenames, environment values, hostnames, serial numbers, credentials, or user account data.
