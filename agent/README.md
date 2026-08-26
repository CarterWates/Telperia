# Telperia Agent

Local-first Phase 8 agent scaffold.

The Telperia Agent is separate from the Evaluation Runner:

- The Evaluation Runner performs controlled benchmark sessions and creates evaluation result packages.
- The Agent is for normal model-use telemetry and non-content inference events.
- They may share telemetry modules, but they should remain separate programs.

## Current Status

Step 27 adds the first Agent v0.1 local collection records. It does not connect
to Supabase, upload data, require an account, or run continuously yet.

Current defaults:

- Mode: `private`
- Upload: disabled
- Research Contribution Mode: disabled
- Prompt capture: disabled
- Response capture: disabled

## Local Event Export

The `record-once` command writes one non-content inference event to JSONL:

```bash
python3 agent/agent.py record-once \
  --output .local/telperia-agent/events.jsonl \
  --request-id local-request-1 \
  --model-id llama3.1:8b \
  --latency-ms 250 \
  --input-tokens 12 \
  --output-tokens 18
```

The output event follows `schemas/inference-event.schema.json` and contains:

- Request id.
- Start and end timestamps.
- Latency.
- Model id.
- Input and output token counts.
- Tokens per second.
- Success status.
- Error category.

It does not contain prompt text, response text, filenames, environment values,
API keys, tokens, passwords, hostnames, serial numbers, local usernames, or
private conversation content.

## Local Snapshot Export

The `snapshot` command writes one local Agent v0.1 record group:

```bash
python3 agent/agent.py snapshot \
  --output .local/telperia-agent/snapshot.jsonl \
  --request-id local-request-1 \
  --model-id llama3.1:8b \
  --latency-ms 250 \
  --input-tokens 12 \
  --output-tokens 18 \
  --inference-engine ollama \
  --runtime-version 0.3.12 \
  --quantization q4_K_M
```

The snapshot contains:

- One inference event.
- One hardware telemetry sample.
- One environment metadata record.

On Mac and non-NVIDIA machines, GPU power, utilization, VRAM, temperature,
driver, and CUDA fields may be `unavailable`, `unknown`, `null`, or zero-valued
placeholders. The agent should report unsupported telemetry honestly instead of
pretending that NVIDIA power telemetry is available.

Environment metadata is limited to non-private fields:

- Operating system.
- GPU model if known or supplied.
- Driver version if known or supplied.
- CUDA version if known or supplied.
- Inference engine.
- Runtime version.
- Quantization.

## Shared Telemetry

The agent imports shared telemetry types and system telemetry helpers from
`evaluation-runner/telperia_telemetry` instead of copying hardware telemetry
structures. Future work can build on that shared package while keeping benchmark
scoring inside the Evaluation Runner.
