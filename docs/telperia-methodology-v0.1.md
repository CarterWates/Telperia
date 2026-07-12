# Telperia Methodology v0.1

## Status

Telperia Methodology v0.1 is the canonical draft methodology for the MVP. It explains what Telperia intends to measure, what data must be preserved, what privacy boundaries apply, and which claims are allowed at each verification level.

This document is intentionally conservative. It includes formulas only where they have been explicitly approved for the MVP. Metrics that need empirical calibration are described as draft, proposed, or deferred rather than treated as final.

## Purpose

Telperia measures local AI model configurations across capability, reliability, efficiency, transparency, and verification context. The MVP exists to help users understand not only whether a model performs well, but also how much energy it used, what hardware it ran on, how repeatable the result is, and how much evidence supports the score.

The MVP should avoid a single universal winner. Different users may care about different tradeoffs: capability, factual reliability, latency, throughput, energy use, hardware fit, openness, and verification quality.

## Methodology Principles

### Versioned Methods

Every score must be tied to a methodology version. If formulas, weights, datasets, scoring rules, or verification requirements change, Telperia should release a new methodology version instead of silently changing old results.

### Raw Data Before Scores

Raw measurements must remain separate from calculated scores. A result package should preserve the inputs needed to audit each score, including benchmark task outcomes, telemetry samples, energy readings, performance measurements, model metadata, hardware metadata, runner version, and verification level.

### Repeatability Over Quantity

The initial dataset should prioritize repeatable measurements over a large number of weakly documented results. Telperia should not publish a stable score for a model configuration until repeated runs produce reasonably consistent capability, energy, runtime, and error measurements.

### Hardware-Specific Interpretation

Efficiency and performance results are hardware-specific. IPW, latency, throughput, VRAM use, and power draw should be compared only against similar hardware and model configuration categories unless the UI clearly explains the difference.

### Privacy By Default

Local evaluation must not require account creation or network access. Prompt text, response text, filenames, environment variables, API keys, tokens, and passwords must not be collected by default. Uploaded results must remain private unless the user explicitly chooses public submission.

## Core Measurement Objects

### Model Configuration

A model configuration should identify:

- Model name.
- Model revision or version.
- Quantization.
- Runtime or inference engine.
- Runtime version when available.
- Relevant configuration values required to reproduce the run.

### Hardware Profile

A hardware profile should identify:

- GPU model.
- GPU count.
- Driver version.
- CUDA version when applicable.
- System memory.
- Operating system when available.
- Relevant runtime environment metadata.

### Evaluation Run

An evaluation run should preserve:

- Run identifier.
- Timestamp.
- Methodology version.
- Evaluation suite version.
- Runner version.
- Model configuration.
- Runtime information.
- Hardware profile.
- Completed task count.
- Total task count.
- Raw benchmark results.
- Calculated scores.
- Energy measurements.
- Performance measurements.
- Error counts.
- Verification level.

## TCI v0.1: Telperia Capability Index

### Status

TCI v0.1 is approved for MVP implementation using the category weights and aggregation formula below.

### What TCI Measures

TCI is intended to measure model capability across the MVP evaluation categories:

- Reasoning.
- Coding.
- Mathematics.
- Factual knowledge.
- Long-context and instruction tasks.

TCI should describe performance on a controlled evaluation suite, not general intelligence, product usefulness, safety, or universal model quality.

### Required Preserved Values

TCI implementations must preserve:

- Raw benchmark score.
- Normalized benchmark score.
- Category score.
- Category weight.
- Final TCI score.
- Completed tasks.
- Total tasks.
- Error count.
- Methodology version.
- Evaluation suite version.

### Categories and Weights

| Category | Weight |
| --- | ---: |
| Reasoning | 25% |
| Coding | 25% |
| Mathematics | 20% |
| Factual Knowledge | 15% |
| Long-Context and Instruction Tasks | 15% |

### Normalization

Each raw benchmark score must be normalized to a 0-100 scale before category aggregation.

```text
Normalized Score = 100 * (Model Score - Reference Floor) / (Reference Ceiling - Reference Floor)
```

For the first MVP suite, task scores are bounded from 0 to 1. The runner uses a reference floor of `0`, a reference ceiling of `1`, and a clipping range of `0` to `100`.

### Formula

```text
TCI v0.1 =
0.25 * Reasoning Score
+ 0.25 * Coding Score
+ 0.20 * Mathematics Score
+ 0.15 * Factual Knowledge Score
+ 0.15 * Long-Context and Instruction Score
```

TCI should be calculated from category-level scores rather than only a final aggregate. This allows users to see whether a model is strong in coding but weak in factual knowledge, or efficient but less capable in mathematics.

## TRI v0.1: Telperia Reliability Index

### Status

TRI v0.1 is deferred for implementation. The MVP website may explain the concept, but runner and backend code should not calculate TRI until the reliability methodology is approved.

### What TRI Should Measure

TRI is reserved for reliability behavior across repeated or operational use. It may eventually include measurements such as:

- Run-to-run stability.
- Error rate.
- Completion consistency.
- Latency consistency.
- Output format adherence.
- Recovery from runtime failures.

### Implementation Rule

Do not calculate or publish TRI values until Telperia has an approved TRI methodology version.

## IPW v0.1: Intelligence Per Watt-Hour

### Status

IPW v0.1 is approved for MVP implementation using the formula below.

### What IPW Measures

IPW measures capability delivered per watt-hour for a completed evaluation run on specific hardware. It is intended to compare efficiency among similar model and hardware configurations, not to declare one universal best model.

### Energy Calculation

GPU energy should be calculated by integrating power readings over time.

For one-second sampling:

```text
GPU Energy in Wh = Sum of Power Readings in Watts / 3600
```

For variable sampling intervals:

```text
GPU Energy in Wh = Sum of Power Reading * Interval in Seconds / 3600
```

Raw power samples must be preserved alongside the final energy calculation.

### IPW Formula

```text
IPW = TCI * Completion Ratio / GPU Energy in Wh
Displayed IPW = 1000 * TCI * Completion Ratio / GPU Energy in Wh
```

The unscaled IPW value must always be preserved. The displayed IPW value is a scaled presentation score and must not replace the unscaled value.

### Required Preserved Values

IPW results must preserve:

- TCI input.
- Completion ratio.
- GPU energy in watt-hours.
- Unscaled IPW.
- Displayed IPW when shown.
- Raw power samples.
- Sampling interval.
- Average power.
- Peak power.
- Hardware profile.
- Methodology version.

## Factual Reliability v0.1

### Status

Factual Reliability v0.1 is approved for MVP implementation for standardized factual question answering tasks.

### What Factual Reliability Measures

Factual Reliability measures whether a model answers factual evaluation questions correctly, incorrectly, or by abstaining. It distinguishes a wrong answer from a refusal or uncertainty response when the evaluation design allows abstention. It should not be described as a total hallucination rate.

### Required Preserved Values

Implementations must preserve:

- Correct responses.
- Incorrect responses.
- Abstentions.
- Total questions.
- Correctness rate.
- Incorrect answer rate.
- Abstention rate.
- Attempted accuracy.

### Formulas

```text
Correctness Rate = Correct Responses / Total Questions
Incorrect Answer Rate = Incorrect Responses / Total Questions
Abstention Rate = Abstentions / Total Questions
Attempted Accuracy = Correct Responses / Attempted Responses
```

Attempted responses are correct plus incorrect responses. Abstentions are excluded from attempted accuracy. The exact handling of partial credit, ambiguous answers, and grader disagreement can be refined in later methodology versions.

## Transparency Score v0.1

### Status

Transparency Score v0.1 is a draft scaffold. The final evidence categories and scoring weights must be explicitly approved before implementation.

### What Transparency Should Measure

Transparency should describe the evidence available behind a model result. It should not reward capability directly. It should help users understand how inspectable, reproducible, and well-documented a score is.

### Candidate Evidence Categories

Transparency may consider:

- Model source and availability.
- Model revision clarity.
- License clarity.
- Quantization metadata.
- Runtime version metadata.
- Hardware metadata completeness.
- Evaluation suite version.
- Runner version.
- Methodology version.
- Availability of raw result package.
- Availability of raw telemetry.
- Verification level.

### Implementation Rule

Do not calculate Transparency Score values until the evidence categories and scoring rules are approved. Public results should still expose the underlying evidence fields wherever available.

## Bias Evaluation v0.1

### Status

Bias Evaluation v0.1 is deferred for implementation.

### Purpose

Bias evaluation is reserved for future Telperia methodology work. It should not be treated as complete in the MVP foundation, and no bias score should be published without an approved evaluation design.

### Implementation Rule

Do not calculate or publish bias evaluation scores until Telperia has an approved bias evaluation methodology version.

## Verification Levels

### Purpose

Verification levels describe how much evidence supports a result. They are not a guarantee that a model is safe, unbiased, tamper-proof, or universally superior.

### Draft Level Definitions

- Level 0: Self-reported result with limited or incomplete metadata.
- Level 1: Result package validates against the supported schema and includes required methodology metadata.
- Level 2: Result includes local telemetry, raw benchmark results, hardware metadata, runner version, and energy measurements.
- Level 3: Result is repeatable across multiple runs with documented variation and no unresolved validation warnings.
- Level 4: Result is produced or reviewed by Telperia under a controlled process that is documented publicly.

### Community Submission Rule

Community submissions may be labeled `Community Measured`. They must not be described as tamper-proof or Telperia Verified unless a later approved verification process supports that claim.

## Privacy And Data Handling

### Local Evaluation

The evaluation runner should run locally without requiring an account or network connection. It should generate a result package that the user can inspect before upload.

### Upload Defaults

Uploaded results should remain private by default. Public submission must be an explicit user choice.

### Prohibited Default Collection

Telperia must not collect the following by default:

- Prompt text.
- Model response text.
- Filenames.
- Environment variables.
- API keys.
- Tokens.
- Passwords.
- Private conversation content.

### Privacy Modes

The Telperia Agent should eventually support:

- Private Mode: no cloud upload.
- Personal Cloud Mode: encrypted metrics uploaded to the user's private dashboard.
- Research Contribution Mode: selected anonymized data contributed to public aggregate research by explicit opt-in.

Research Contribution Mode must be disabled by default.

## Known Limitations

The MVP intentionally does not include:

- Native iOS application.
- Enterprise billing.
- Team workspaces.
- Kubernetes integration.
- AMD support.
- Apple Silicon support.
- Distributed inference.
- Prompt collection.
- Response collection.
- Automatic hallucination analysis of private conversations.
- Carbon claims without reliable methodology.
- One universal model ranking.
- Autonomous model optimization.
- Proprietary hardware.
- Complex AI recommendations.
- Mobile push notifications.

## Publication Rules

Every public score should display or link to:

- Methodology version.
- Verification level.
- Hardware profile.
- Model configuration.
- Evaluation suite version.
- Runner version.
- Known limitations.
- Raw measurements or downloadable result package when available.

Telperia should avoid unsupported claims such as:

- One universal best model.
- Tamper-proof community measurements.
- Carbon impact claims without a reliable carbon methodology.
- Private conversation hallucination analysis without explicit consent and a separate approved privacy model.

## Relationship To Split Methodology Files

This document is the canonical human-readable methodology draft. The files in `methodology/` are implementation-facing extracts for specific methods and policies. When this document changes, the relevant split files should be updated in the same or a clearly linked follow-up change.
