from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib import request
from urllib.error import URLError


@dataclass(frozen=True)
class GenerationResult:
    text: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    success: bool
    error_category: str | None


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", opener: Any | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._opener = opener or request

    def version(self, timeout: float = 5.0) -> str:
        try:
            with self._open(f"{self.base_url}/api/version", timeout=timeout) as response:
                payload = json.loads(response.read().decode())
        except (OSError, URLError, TimeoutError) as exc:
            raise ConnectionError("Ollama service is unavailable") from exc
        return str(payload.get("version", "unknown"))

    def generate(self, model: str, prompt: str, timeout: float = 120.0) -> GenerationResult:
        body = json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode()
        req = request.Request(
            f"{self.base_url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        try:
            with self._open(req, timeout=timeout) as response:
                payload = json.loads(response.read().decode())
        except TimeoutError:
            return _failed_result(started, "timeout")
        except (OSError, URLError, json.JSONDecodeError):
            return _failed_result(started, "runtime_error")

        if payload.get("error"):
            return _failed_result(started, "ollama_error")

        return GenerationResult(
            text=str(payload.get("response", "")),
            latency_ms=(time.perf_counter() - started) * 1000.0,
            input_tokens=int(payload.get("prompt_eval_count", 0) or 0),
            output_tokens=int(payload.get("eval_count", 0) or 0),
            success=True,
            error_category=None,
        )

    def _open(self, target: Any, timeout: float):
        if hasattr(self._opener, "open"):
            return self._opener.open(target, timeout=timeout)
        return self._opener.urlopen(target, timeout=timeout)


def _failed_result(started: float, error_category: str) -> GenerationResult:
    return GenerationResult(
        text="",
        latency_ms=(time.perf_counter() - started) * 1000.0,
        input_tokens=0,
        output_tokens=0,
        success=False,
        error_category=error_category,
    )
