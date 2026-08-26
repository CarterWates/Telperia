from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4


PRIVATE_FIELD_NAMES = {
    "prompt",
    "prompts",
    "prompt_text",
    "prompttext",
    "response",
    "responses",
    "response_text",
    "responsetext",
    "content",
    "filename",
    "file_path",
    "environment",
    "env",
    "api_key",
    "apikey",
    "token",
    "password",
    "secret",
    "hostname",
    "serial_number",
    "serialnumber",
    "username",
}


def build_inference_event(
    *,
    model_id: str,
    latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    success: bool,
    request_id: str | None = None,
    start_time: datetime | None = None,
    error_category: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if extra_fields:
        _reject_private_fields(extra_fields)
    if not model_id:
        raise ValueError("model_id is required")
    if latency_ms < 0:
        raise ValueError("latency_ms must be nonnegative")
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts must be nonnegative")

    started_at = start_time or datetime.now(UTC)
    ended_at = started_at + timedelta(milliseconds=latency_ms)
    seconds = latency_ms / 1000.0
    tokens_per_second = output_tokens / seconds if seconds > 0 else 0.0

    return {
        "request_id": request_id or str(uuid4()),
        "start_time": _format_timestamp(started_at),
        "end_time": _format_timestamp(ended_at),
        "latency_ms": float(latency_ms),
        "model_id": model_id,
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "tokens_per_second": tokens_per_second,
        "success": bool(success),
        "error_category": None if success else (error_category or "unknown_error"),
    }


def _reject_private_fields(payload: dict[str, Any], path: str = "$") -> None:
    for key, value in payload.items():
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in PRIVATE_FIELD_NAMES:
            raise ValueError(f"private content field is not allowed at {path}.{key}")
        if isinstance(value, dict):
            _reject_private_fields(value, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    _reject_private_fields(item, f"{path}.{key}[{index}]")


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
