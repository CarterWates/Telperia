from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from telperia_api.ingestion_service import InMemoryIngestionStore, ingest_result_request


DEFAULT_USER_ID = "local-dev-user"
INGEST_PATH = "/api/results/ingest"


@dataclass(frozen=True)
class LocalApiConfig:
    schema_path: Path
    store: InMemoryIngestionStore = field(default_factory=InMemoryIngestionStore)
    default_user_id: str = DEFAULT_USER_ID


@dataclass(frozen=True)
class LocalHttpResponse:
    status_code: int
    payload: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)


def handle_local_request(
    method: str,
    path: str,
    headers: Mapping[str, str],
    body: bytes,
    config: LocalApiConfig,
) -> LocalHttpResponse:
    route = urlparse(path).path
    normalized_method = method.upper()

    if normalized_method == "GET" and route == "/health":
        return LocalHttpResponse(
            status_code=200,
            payload={
                "status": "ok",
                "service": "telperia-api",
                "mode": "local",
                "storage": "memory",
                "supabase": "disabled",
            },
        )

    if normalized_method == "POST" and route == INGEST_PATH:
        request_body = _decode_json_body(body)
        if request_body is None:
            return _rejected(400, "invalid_request_body", "Request body must be valid JSON.")
        response = ingest_result_request(
            request_body,
            user_id=_local_user_id(headers, config),
            schema_path=config.schema_path,
            store=config.store,
        )
        return LocalHttpResponse(status_code=response.status_code, payload=response.payload)

    return _rejected(404, "not_found", "Endpoint not found.")


def create_request_handler(config: LocalApiConfig) -> type[BaseHTTPRequestHandler]:
    class TelperiaLocalRequestHandler(BaseHTTPRequestHandler):
        server_version = "TelperiaLocalAPI/0.1"

        def do_GET(self) -> None:
            self._handle()

        def do_POST(self) -> None:
            self._handle()

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _handle(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length) if content_length else b""
            response = handle_local_request(self.command, self.path, self.headers, body, config)
            self._send_json(response)

        def _send_json(self, response: LocalHttpResponse) -> None:
            encoded = json.dumps(response.payload, sort_keys=True).encode("utf-8")
            self.send_response(response.status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(encoded)

    return TelperiaLocalRequestHandler


def run_local_api(*, host: str, port: int, schema_path: Path) -> None:
    config = LocalApiConfig(schema_path=schema_path)
    handler = create_request_handler(config)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Telperia local API listening on http://{host}:{port}", flush=True)
    print("Supabase writes are disabled; accepted uploads are stored in memory only.", flush=True)
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Telperia Phase 6 API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "schemas" / "evaluation-run.schema.json",
        help="Path to schemas/evaluation-run.schema.json.",
    )
    args = parser.parse_args()
    try:
        run_local_api(host=args.host, port=args.port, schema_path=args.schema)
    except KeyboardInterrupt:
        print("\nTelperia local API stopped.", flush=True)


def _decode_json_body(body: bytes) -> dict[str, Any] | None:
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return decoded if isinstance(decoded, dict) else None


def _local_user_id(headers: Mapping[str, str], config: LocalApiConfig) -> str:
    for key, value in headers.items():
        if key.lower() == "x-telperia-user-id" and value.strip():
            return value.strip()
    return config.default_user_id


def _rejected(status_code: int, error_code: str, message: str) -> LocalHttpResponse:
    return LocalHttpResponse(
        status_code=status_code,
        payload={
            "ingestion_status": "rejected",
            "error_code": error_code,
            "message": message,
        },
    )


if __name__ == "__main__":
    main()
