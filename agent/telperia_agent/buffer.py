from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from telperia_agent.privacy import PrivacySettings


BUFFER_FILENAME = "agent-buffer.jsonl"
STATE_FILENAME = "agent-state.json"


class BufferLimitError(RuntimeError):
    pass


class AgentBuffer:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.buffer_path = output_dir / BUFFER_FILENAME
        self.state_path = output_dir / STATE_FILENAME

    def append(
        self,
        record_type: str,
        data: dict[str, Any],
        privacy: PrivacySettings,
        *,
        max_storage_bytes: int | None = None,
        created_at: datetime | None = None,
    ) -> dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        content_hash = stable_content_hash(record_type, data, privacy)
        existing = self._find_by_hash(content_hash)
        if existing is not None:
            duplicate = dict(existing)
            duplicate["buffer"] = dict(existing["buffer"])
            duplicate["buffer"]["duplicate"] = True
            return duplicate

        record = {
            "record_type": record_type,
            "privacy": privacy.to_dict(),
            "buffer": {
                "local_record_id": content_hash[:32],
                "created_at": _format_timestamp(created_at or datetime.now(UTC)),
                "upload_status": "not_configured",
                "upload_attempt_count": 0,
                "content_hash": content_hash,
                "duplicate": False,
            },
            "data": data,
        }
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
        if max_storage_bytes is not None and self.agent_owned_size_bytes() + len(encoded.encode("utf-8")) > max_storage_bytes:
            raise BufferLimitError("Agent local storage limit reached before writing new records.")

        with self.buffer_path.open("a", encoding="utf-8") as handle:
            handle.write(encoded)
        return record

    def read_records(self) -> list[dict[str, Any]]:
        if not self.buffer_path.exists():
            return []
        return [json.loads(line) for line in self.buffer_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def status(self) -> dict[str, Any]:
        records = self.read_records()
        pending = [record for record in records if record.get("buffer", {}).get("upload_status") == "not_configured"]
        return {
            "privacy_mode": "private",
            "upload_status": "not_configured",
            "pending_count": len(pending),
            "record_count": len(records),
            "storage_bytes": self.agent_owned_size_bytes(),
        }

    def delete_local_data(self) -> int:
        deleted = 0
        for path in (self.buffer_path, self.state_path):
            if path.exists():
                path.unlink()
                deleted += 1
        return deleted

    def pause(self) -> None:
        self._write_state(paused=True)

    def resume(self) -> None:
        self._write_state(paused=False)

    def is_paused(self) -> bool:
        if not self.state_path.exists():
            return False
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return bool(payload.get("paused", False))

    def agent_owned_size_bytes(self) -> int:
        total = 0
        for path in (self.buffer_path, self.state_path):
            if path.exists():
                total += path.stat().st_size
        return total

    def _find_by_hash(self, content_hash: str) -> dict[str, Any] | None:
        for record in self.read_records():
            if record.get("buffer", {}).get("content_hash") == content_hash:
                return record
        return None

    def _write_state(self, *, paused: bool) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        payload = {"paused": paused, "updated_at": _format_timestamp(datetime.now(UTC))}
        self.state_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def stable_content_hash(record_type: str, data: dict[str, Any], privacy: PrivacySettings) -> str:
    payload = {
        "record_type": record_type,
        "privacy": privacy.to_dict(),
        "data": data,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
