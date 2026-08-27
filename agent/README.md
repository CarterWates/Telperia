# Telperia Agent

Local-first Phase 8 agent scaffold.

The Telperia Agent is separate from the Evaluation Runner:

- The Evaluation Runner performs controlled benchmark sessions and creates evaluation result packages.
- The Agent is for normal model-use telemetry and non-content inference events.
- They may share telemetry modules, but they should remain separate programs.

## Current Status

Step 29 adds local buffering and a simple local runtime loop on top of the
Agent privacy modes and v0.1 local collection records. It does not connect to
Supabase, upload data, require an account, or run as a packaged background
service yet.

Current defaults:

- Mode: `private`
- Upload: disabled
- Research Contribution Mode: disabled
- Prompt capture: disabled
- Response capture: disabled

## Privacy Modes

Private Mode is the only active mode today:

- Local JSONL export only.
- No cloud upload.
- No account required.
- No network required.
- No prompt or response content collected.

Personal Cloud Mode is planned for encrypted metrics in a user's private
dashboard. It is recognized by the CLI, but upload is blocked until backend
support exists.

Research Contribution Mode is planned for selected anonymized data contributed
to public aggregate research. It is disabled by default, requires an explicit
opt-in flag to inspect, and still cannot upload data in the current MVP.

Check the current default privacy settings:

```bash
python3 agent/agent.py privacy-status
```

## Local Event Export

The `record-once` command writes one non-content inference event to JSONL:

```bash
python3 agent/agent.py record-once \
  --output .local/telperia-agent/events.jsonl \
  --request-id local-request-1 \
  --model-id llama3.1:8b \
  --latency-ms 250 \
  --input-tokens 12 \
  --output-tokens 18 \
  --privacy-mode private
```

The exported record includes privacy metadata plus an inference event that
follows `schemas/inference-event.schema.json` and contains:

- Request id.
- Start and end timestamps.
- Latency.
- Model id.
- Input and output token counts.
- Tokens per second.
- Success status.
- Error category.

It does not contain prompt text, response text, filenames, environment variables,
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
  --quantization q4_K_M \
  --privacy-mode private
```

The snapshot contains:

- One inference event.
- One hardware telemetry sample.
- One environment metadata record.
- Private Mode metadata showing upload is disabled.

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

## Local Runtime And Buffer

Run a short local loop:

```bash
python3 agent/agent.py run \
  --output-dir .local/telperia-agent \
  --interval-seconds 1 \
  --max-samples 3 \
  --model-id llama3.1:8b \
  --inference-engine ollama
```

The runtime writes Agent-owned local records to:

```text
.local/telperia-agent/agent-buffer.jsonl
```

Each buffered record includes:

- `record_type`
- privacy metadata
- buffer metadata with local record id, created timestamp, upload status, upload attempt count, and content hash
- non-content telemetry data

Uploads are still disabled. Buffer records use `upload_status: not_configured`
and `upload_attempt_count: 0` so future retry behavior has a safe place to start
without creating a network path today.

Check pending local records:

```bash
python3 agent/agent.py buffer-status --output-dir .local/telperia-agent
```

Pause or resume collection:

```bash
python3 agent/agent.py pause --output-dir .local/telperia-agent
python3 agent/agent.py resume --output-dir .local/telperia-agent
```

Delete Agent-owned local files:

```bash
python3 agent/agent.py delete-local-data --output-dir .local/telperia-agent --confirm
```

The delete command removes only Agent-owned files in the chosen output
directory: `agent-buffer.jsonl` and `agent-state.json`.

Show collected fields:

```bash
python3 agent/agent.py collected-fields
```
