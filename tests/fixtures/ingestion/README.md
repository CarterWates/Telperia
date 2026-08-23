# Ingestion Fixtures

These fixtures exercise Phase 6 result ingestion behavior without requiring Supabase, a network connection, or a live model.

- `valid_private_upload.json`: schema-valid package that should be accepted with low energy confidence and level-zero verification warnings.
- `rejected_prompt_response_content.json`: schema-valid package containing disallowed prompt and response keys under an extensible score object.
- `invalid_ipw_math.json`: schema-valid package with Local IPW values that do not match TCI, completion ratio, and GPU energy.
- `duplicate_run_id_original.json`: first package in a same-run-id duplicate pair.
- `duplicate_run_id_changed.json`: second package in the duplicate pair with the same `run_id` but different content.
- `low_energy_confidence_warning.json`: accepted package that should preserve a low energy confidence warning.

The duplicate pair is intentionally accepted by the local package validator because duplicate detection requires backend ownership and package-hash state.
