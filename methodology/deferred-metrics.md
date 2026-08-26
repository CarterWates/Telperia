# Deferred Metrics Policy

## Status

Approved guidance for Telperia MVP presentation. This document does not introduce new score formulas.

## Purpose

Some Telperia concepts are important to the product direction but are not approved scoring methods yet. The Observatory may explain these concepts, but it must not display them as numeric scores until a complete methodology is approved.

## Active MVP Scores

The MVP may display these as active metrics:

- TCI v0.1.
- Factual Reliability v0.1.
- Local IPW v0.1.
- Verification Level.

Every active score should link to its methodology version or evidence-quality definition.

## Deferred MVP Scores

These should not be displayed as numeric scores in the MVP:

- TRI v0.1.
- Transparency Score v0.1.
- Bias Evaluation v0.1.

The website may describe them as planned, deferred, or methodology pending.

## Approved Presentation Language

For TRI:

```text
TRI, or Telperia Reliability Index, is a planned reliability metric for measuring consistency, operational stability, completion behavior, and repeatability across runs. TRI is not currently calculated in MVP results.
```

Short labels:

- `TRI: Not yet scored`
- `Reliability Index: methodology pending`
- `Planned metric`

For transparency:

```text
Transparency evidence records what is known about a model or result package, such as methodology version, model revision, hardware metadata, runner version, raw measurement availability, verification level, and whether the result can be independently inspected. Telperia does not yet publish a single Transparency Score.
```

Short labels:

- `Transparency Evidence`
- `Score pending`
- `Evidence available`

## Implementation Rule

Runner, backend, and website code must not calculate or publish numeric TRI or Transparency Score values until their formulas, evidence categories, and scoring rules are approved in methodology documents.

It is acceptable to show the underlying evidence fields directly. Do not collapse those fields into a score without an approved methodology.
