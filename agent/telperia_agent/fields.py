from __future__ import annotations

from typing import Any


def collected_fields_manifest() -> dict[str, Any]:
    return {
        "hardware": [
            "gpu.utilization_percent",
            "gpu.vram_used_mb",
            "gpu.vram_total_mb",
            "gpu.power_draw_w",
            "gpu.temperature_c",
            "cpu_utilization_percent",
            "system_memory_used_mb",
        ],
        "inference": [
            "request_id",
            "start_time",
            "end_time",
            "latency_ms",
            "model_id",
            "input_tokens",
            "output_tokens",
            "tokens_per_second",
            "success",
            "error_category",
        ],
        "environment": [
            "operating_system",
            "gpu_model",
            "driver_version",
            "cuda_version",
            "inference_engine",
            "runtime_version",
            "quantization",
        ],
        "local_metadata": [
            "record_type",
            "privacy.mode",
            "privacy.upload_enabled",
            "privacy.upload_policy",
            "buffer.local_record_id",
            "buffer.created_at",
            "buffer.upload_status",
            "buffer.upload_attempt_count",
            "buffer.content_hash",
        ],
        "never_collected": [
            "prompt",
            "prompt_text",
            "response",
            "response_text",
            "filenames",
            "environment_variables",
            "api_keys",
            "tokens",
            "passwords",
            "private_keys",
            "hostnames",
            "serial_numbers",
            "local_usernames",
            "private_conversation_content",
        ],
    }
