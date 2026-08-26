from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from telperia_runner.ingestion import extract_observatory_row, validate_ingestion_package


ALLOWED_VISIBILITIES = {"private", "submit_for_public_review"}
SAFE_STORAGE_SEGMENT = re.compile(r"^[A-Za-z0-9_-]+$")
VALIDATION_ERROR_STATUS = {
    "invalid_schema": 422,
    "unsupported_schema_version": 422,
    "unsupported_methodology_version": 422,
    "unsupported_evaluation_suite": 422,
    "privacy_violation": 422,
    "metric_consistency_error": 422,
    "energy_consistency_error": 422,
}


@dataclass(frozen=True)
class IngestionResponse:
    status_code: int
    payload: dict[str, Any]


@dataclass(frozen=True)
class StoredIngestionRecord:
    upload_id: str
    user_id: str
    run_id: str
    package_hash: str
    storage_path: str
    raw_package: dict[str, Any]
    observatory_summary: dict[str, Any]
    visibility: str
    validation_warnings: list[str]


class IngestionStore(Protocol):
    def get_by_run_id(self, run_id: str) -> StoredIngestionRecord | None:
        ...

    def save(self, record: StoredIngestionRecord) -> None:
        ...


class InMemoryIngestionStore:
    def __init__(self) -> None:
        self._records_by_run_id: dict[str, StoredIngestionRecord] = {}

    def get_by_run_id(self, run_id: str) -> StoredIngestionRecord | None:
        return self._records_by_run_id.get(run_id)

    def save(self, record: StoredIngestionRecord) -> None:
        self._records_by_run_id[record.run_id] = record


def ingest_result_request(
    body: dict[str, Any],
    *,
    user_id: str | None,
    schema_path: Path,
    store: IngestionStore | None = None,
) -> IngestionResponse:
    if not user_id:
        return _rejected(401, "unauthenticated", "Authentication is required to upload result packages.")
    if not _is_safe_storage_segment(user_id):
        return _rejected(400, "invalid_request_body", "Authenticated user id must be a safe storage segment.")

    request_error = _validate_request_body(body)
    if request_error is not None:
        return request_error

    result_package = body["result_package"]
    visibility = body.get("visibility", "private")
    validation = validate_ingestion_package(result_package, schema_path)
    if not validation.accepted:
        return _rejected(
            VALIDATION_ERROR_STATUS.get(validation.error_code or "", 422),
            validation.error_code or "invalid_schema",
            validation.message,
        )

    active_store = store or InMemoryIngestionStore()
    package_hash = canonical_package_hash(result_package)
    run_id = result_package["run_id"]
    existing = active_store.get_by_run_id(run_id)
    if existing is not None:
        if existing.package_hash != package_hash or existing.user_id != user_id:
            return _rejected(409, "duplicate_run_id", "A different result package already exists for this run_id.")
        payload = _accepted_payload(existing, duplicate=True)
        return IngestionResponse(status_code=200, payload=payload)

    upload_id = str(uuid4())
    storage_path = storage_path_for(user_id=user_id, run_id=run_id)
    record = StoredIngestionRecord(
        upload_id=upload_id,
        user_id=user_id,
        run_id=run_id,
        package_hash=package_hash,
        storage_path=storage_path,
        raw_package=result_package,
        observatory_summary=extract_observatory_row(result_package, result_id=upload_id),
        visibility=visibility,
        validation_warnings=validation.validation_warnings,
    )
    active_store.save(record)

    return IngestionResponse(status_code=201, payload=_accepted_payload(record))


def canonical_package_hash(package: dict[str, Any]) -> str:
    canonical_json = json.dumps(package, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def storage_path_for(*, user_id: str, run_id: str) -> str:
    if not _is_safe_storage_segment(user_id) or not _is_safe_storage_segment(run_id):
        raise ValueError("Storage path segments must contain only letters, numbers, underscores, and hyphens.")
    return f"result-packages/users/{user_id}/runs/{run_id}.json"


def _validate_request_body(body: dict[str, Any]) -> IngestionResponse | None:
    if not isinstance(body, dict):
        return _rejected(400, "invalid_request_body", "Request body must be a JSON object.")
    if "result_package" not in body or not isinstance(body["result_package"], dict):
        return _rejected(400, "invalid_request_body", "Request body must contain one result_package object.")

    extra_keys = set(body) - {"result_package", "visibility"}
    if extra_keys:
        return _rejected(400, "invalid_request_body", "Request body contains unsupported fields.")

    visibility = body.get("visibility", "private")
    if visibility == "public":
        return _rejected(400, "invalid_visibility", "Direct public visibility is not allowed on upload.")
    if visibility not in ALLOWED_VISIBILITIES:
        return _rejected(400, "invalid_visibility", "Visibility must be private or submit_for_public_review.")

    return None


def _accepted_payload(record: StoredIngestionRecord, *, duplicate: bool = False) -> dict[str, Any]:
    payload = {
        "upload_id": record.upload_id,
        "run_id": record.run_id,
        "ingestion_status": "accepted",
        "visibility": _response_visibility(record.visibility),
        "validation_warnings": record.validation_warnings,
    }
    if duplicate:
        payload["duplicate"] = True
    if record.visibility == "submit_for_public_review":
        payload["public_submission_status"] = "pending_review"
    return payload


def _response_visibility(visibility: str) -> str:
    if visibility == "submit_for_public_review":
        return "submitted_for_public_review"
    return visibility


def _is_safe_storage_segment(value: str) -> bool:
    return bool(SAFE_STORAGE_SEGMENT.fullmatch(value))


def _rejected(status_code: int, error_code: str, message: str) -> IngestionResponse:
    return IngestionResponse(
        status_code=status_code,
        payload={
            "ingestion_status": "rejected",
            "error_code": error_code,
            "message": message,
        },
    )
