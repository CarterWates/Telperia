# TCI v0.1

## Status

Approved for MVP implementation as TCI v0.1.

## Purpose

TCI measures demonstrated capability across the versioned Telperia evaluation suite. It does not claim to measure general intelligence, safety, usefulness, or universal model quality.

## Categories and Weights

| Category | Weight |
| --- | ---: |
| Reasoning | 25% |
| Coding | 25% |
| Mathematics | 20% |
| Factual Knowledge | 15% |
| Long-Context and Instruction Tasks | 15% |

The MVP runner maps the Long-Context and Instruction Tasks category to `instruction_adherence` tasks in the `tci-v0.1` suite.

## Normalization

Each raw benchmark score is normalized to a 0-100 scale before category aggregation.

```text
Normalized Score = 100 * (Model Score - Reference Floor) / (Reference Ceiling - Reference Floor)
```

For the first MVP suite, task scores are already bounded from 0 to 1. The runner therefore uses:

- Reference floor: `0`
- Reference ceiling: `1`
- Clipping range: `0` to `100`

## Formula

```text
TCI v0.1 =
0.25 * Reasoning Score
+ 0.25 * Coding Score
+ 0.20 * Mathematics Score
+ 0.15 * Factual Knowledge Score
+ 0.15 * Long-Context and Instruction Score
```

All category scores are normalized to a 0-100 scale before aggregation.

## Implementation Rule

The runner must preserve raw benchmark scores, normalized benchmark scores, category scores, category weights, and the final TCI score separately. Telperia should not publish only the final TCI number.
