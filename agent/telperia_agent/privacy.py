from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PRIVATE_MODE = "private"
PERSONAL_CLOUD_MODE = "personal_cloud"
RESEARCH_CONTRIBUTION_MODE = "research_contribution"

SUPPORTED_PRIVACY_MODES = {
    PRIVATE_MODE,
    PERSONAL_CLOUD_MODE,
    RESEARCH_CONTRIBUTION_MODE,
}


class PrivacyModeError(ValueError):
    pass


@dataclass(frozen=True)
class PrivacySettings:
    mode: str
    status: str
    upload_enabled: bool
    upload_policy: str
    research_contribution_enabled: bool
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "status": self.status,
            "upload_enabled": self.upload_enabled,
            "upload_policy": self.upload_policy,
            "research_contribution_enabled": self.research_contribution_enabled,
            "description": self.description,
        }


def resolve_privacy_settings(
    mode: str | None = None,
    *,
    research_contribution_enabled: bool = False,
) -> PrivacySettings:
    normalized_mode = normalize_privacy_mode(mode)
    if normalized_mode == PRIVATE_MODE:
        return PrivacySettings(
            mode=PRIVATE_MODE,
            status="active",
            upload_enabled=False,
            upload_policy="disabled",
            research_contribution_enabled=False,
            description="Private Mode stores local JSONL records only and never uploads data.",
        )
    if normalized_mode == PERSONAL_CLOUD_MODE:
        return PrivacySettings(
            mode=PERSONAL_CLOUD_MODE,
            status="planned_not_connected",
            upload_enabled=False,
            upload_policy="blocked_until_backend_available",
            research_contribution_enabled=False,
            description="Personal Cloud Mode is planned for encrypted private dashboards, but no cloud upload path exists yet.",
        )
    if normalized_mode == RESEARCH_CONTRIBUTION_MODE:
        if not research_contribution_enabled:
            raise PrivacyModeError("Research Contribution Mode requires explicit opt-in.")
        return PrivacySettings(
            mode=RESEARCH_CONTRIBUTION_MODE,
            status="planned_not_connected",
            upload_enabled=False,
            upload_policy="blocked_until_backend_available",
            research_contribution_enabled=True,
            description="Research Contribution Mode is planned for selected anonymized aggregate research data, but no upload path exists yet.",
        )
    raise PrivacyModeError(f"Unsupported privacy mode: {mode}")


def normalize_privacy_mode(mode: str | None) -> str:
    if mode is None:
        return PRIVATE_MODE
    normalized = mode.strip().lower().replace("-", "_")
    if normalized in SUPPORTED_PRIVACY_MODES:
        return normalized
    raise PrivacyModeError(f"Unsupported privacy mode: {mode}")


def require_local_export_allowed(settings: PrivacySettings) -> None:
    if settings.mode == PRIVATE_MODE:
        return
    raise PrivacyModeError(
        f"{settings.mode} is {settings.status.replace('_', ' ')}; upload and export behavior for this mode is not connected yet."
    )


def wrap_local_record(record_type: str, data: dict[str, Any], settings: PrivacySettings) -> dict[str, Any]:
    return {
        "record_type": record_type,
        "privacy": settings.to_dict(),
        "data": data,
    }
