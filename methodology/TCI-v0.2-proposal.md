# TCI v0.2 Proposal

## Status

Draft proposal only. TCI v0.2 is not approved for MVP scoring and is not implemented by the current evaluation runner.

Current Telperia result packages must continue to use TCI v0.1 unless a future methodology version is explicitly approved, implemented, tested, and labeled in the result schema.

## Purpose

TCI v0.2 should improve the Telperia Capability Index while preserving the core v0.1 idea: capability is measured from a controlled, versioned evaluation suite, not inferred from reputation, model size, or marketing claims.

The main goal of v0.2 is to reduce inflated scores from small or easy benchmark suites and make score interpretation clearer across capability areas.

## Motivation

TCI v0.1 is useful for the MVP because it is simple, auditable, and easy to implement. Its main limitations are:

- A small suite can make weaker models appear stronger than they are.
- Category scores do not yet distinguish between easy, medium, hard, and adversarial tasks.
- Factual performance and calibration are partly mixed into broader capability scoring.
- Some practical tasks need more structured scoring than a single correct or incorrect answer.
- Public comparisons need stronger confidence signals before scores are treated as stable.

TCI v0.2 should address those limits without turning TCI into a vague universal intelligence score.

## Proposed Categories and Weights

| Category | Proposed Weight |
| --- | ---: |
| Factual Reliability | 25% |
| Reasoning | 25% |
| Practical Utility | 20% |
| Instruction Following | 15% |
| Robustness | 10% |
| Calibration | 5% |

These weights are proposed for discussion and calibration. They should not be used in published scoring until the benchmark suite and normalization method are approved.

## Proposed Formula

```text
TCI v0.2 =
0.25 * Factual Reliability Score
+ 0.25 * Reasoning Score
+ 0.20 * Practical Utility Score
+ 0.15 * Instruction Following Score
+ 0.10 * Robustness Score
+ 0.05 * Calibration Score
```

All category scores should be normalized to a 0-100 scale before aggregation. Raw benchmark outputs, normalized benchmark scores, category scores, category weights, and the final TCI value must remain separate.

## Category Definitions

### Factual Reliability

Measures whether the model answers factual tasks correctly, incorrectly, or by abstaining when uncertainty is appropriate. This category should reuse the approved Factual Reliability concepts where possible, including correctness rate, incorrect answer rate, abstention rate, and attempted accuracy.

### Reasoning

Measures multi-step logic, math reasoning, constraint solving, causal reasoning, planning, and consistency across harder tasks. Reasoning tasks should avoid relying only on memorized facts.

### Practical Utility

Measures useful applied performance on coding, extraction, summarization, classification, data interpretation, and structured-output tasks. This category should favor tasks that resemble real work while still being auto-gradable.

### Instruction Following

Measures whether the model obeys format rules, required fields, forbidden content boundaries, ordering constraints, and exact user instructions. This should include tasks where the answer content is easy but the constraint-following is the real test.

### Robustness

Measures performance under ambiguous wording, distracting context, adversarial phrasing, conflicting instructions, and noisy inputs. Robustness tasks should test whether the model can preserve the actual task objective under pressure.

### Calibration

Measures whether the model expresses uncertainty appropriately, abstains when the benchmark allows abstention, and avoids confident false answers. Calibration should not reward blanket refusal; it should reward knowing when to answer and when not to answer.

## Difficulty Tiers

TCI v0.2 should introduce difficulty tiers inside each major category:

| Tier | Intended Use |
| --- | --- |
| Easy | Sanity checks and basic capability coverage. |
| Medium | Normal user tasks that competent local models should attempt. |
| Hard | Tasks that separate strong local models from weaker ones. |
| Adversarial | Tricky, ambiguous, or distracting tasks that test robustness and calibration. |

Published v0.2 category scores should include tier-level subscores so users can see whether a model is broadly competent or mainly performing well on easier tasks.

## Scoring Requirements

TCI v0.2 should preserve:

- Raw task score.
- Normalized task score.
- Task category.
- Task difficulty tier.
- Category score.
- Category weight.
- Tier score where applicable.
- Final TCI v0.2 score.
- Completion ratio.
- Error count.
- Methodology version.
- Evaluation suite version.
- Verification level.

The runner should not save prompt or response content beyond predefined public evaluation prompts and approved public answer keys.

## Benchmark Design Requirements

A v0.2 suite should:

- Be large enough that a single lucky task cannot materially distort the final score.
- Include balanced category coverage.
- Include difficulty tier metadata for every task.
- Prefer deterministic, auto-gradable tasks for the MVP path.
- Separate factual correctness from instruction formatting where possible.
- Include abstention-aware factual questions.
- Include tasks that are difficult enough to challenge frontier models without making local models unusable for comparison.
- Preserve public prompts and answer keys in versioned files.

## Relationship to IPW

TCI v0.2 should remain a capability score. Energy efficiency should stay in IPW.

```text
IPW v0.2 = TCI v0.2 * Completion Ratio / Energy
```

If a scaled display score is used, the unscaled IPW value must still be preserved. Local IPW and any future hosted or data-center IPW must remain separately labeled.

## Migration Notes

TCI v0.1 and TCI v0.2 scores should not be compared as if they are the same metric. If Telperia adopts v0.2 later, public result pages should show methodology versions clearly and either:

- Keep v0.1 and v0.2 leaderboards separate.
- Re-run selected models on the v0.2 suite before showing cross-model v0.2 comparisons.

Historical v0.1 result packages should not be rewritten to appear as v0.2 results.

## Approval Gate

Before TCI v0.2 becomes active, Telperia should complete:

1. A finalized v0.2 benchmark suite.
2. Unit tests for all v0.2 formulas.
3. Schema support for v0.2 fields.
4. Runner implementation behind an explicit suite and methodology version.
5. Validation against existing privacy rules.
6. Several calibration runs across small, mid-size, and stronger models.
7. A clear public note explaining that v0.2 replaces neither old v0.1 data nor the raw measurements behind it.
