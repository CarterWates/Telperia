# Transparency Score v0.1

## Status

Deferred metric. The authoritative transparency score methodology, evidence categories, weights, and scoring rules must be supplied or explicitly approved before implementation.

## Purpose

The Transparency Score is intended to describe the evidence available for model, evaluation, hardware, methodology, and verification claims.

Until the score is approved, Telperia should show transparency evidence directly instead of collapsing it into one number. Useful evidence fields include:

- Methodology version.
- Model revision clarity.
- Quantization metadata.
- Runtime version.
- Hardware metadata completeness.
- Runner version.
- Raw result package availability.
- Raw telemetry availability.
- Verification level.

## Implementation Rule

Do not implement transparency scoring from this scaffold alone. Public results may show transparency evidence, but must not display numeric Transparency Score values until a scoring methodology is approved. Use `methodology/deferred-metrics.md` for approved MVP presentation language.
