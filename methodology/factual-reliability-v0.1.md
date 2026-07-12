# Factual Reliability v0.1

## Status

Approved for MVP implementation as Factual Reliability v0.1.

## Purpose

Factual Reliability is intended to measure correctness, incorrect responses, abstentions, and attempted accuracy for factual evaluation tasks.

It focuses on factual question answering. It should not be described as a total hallucination rate because hallucination can include other behaviors such as fabricated citations, grounding errors, unsupported claims, and summarization inconsistencies.

## Required Raw Values

Future implementations must preserve:

- Correct responses.
- Incorrect responses.
- Abstentions.
- Total questions.
- Correctness rate.
- Incorrect answer rate.
- Abstention rate.
- Attempted accuracy.

## Formulas

```text
Correctness Rate = Correct Responses / Total Questions
Incorrect Answer Rate = Incorrect Responses / Total Questions
Abstention Rate = Abstentions / Total Questions
Attempted Accuracy = Correct Responses / Attempted Responses
```

Attempted responses are correct plus incorrect responses. Abstentions are excluded from attempted accuracy.
