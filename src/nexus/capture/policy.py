from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CapturePolicy:
    """Local policy controlling whether capture may be started."""

    enabled: bool = False
    retention_days: int = 7
    max_storage_bytes: int = 10 * 1024 * 1024 * 1024
    storage_root: Path = Path(".nexus/captures")

    def validate(self) -> None:
        if self.retention_days < 1:
            raise ValueError("retention_days must be at least 1")
        if self.max_storage_bytes < 1:
            raise ValueError("max_storage_bytes must be positive")
        if not self.storage_root.is_absolute() and str(self.storage_root).strip() in {"", "."}:
            raise ValueError("storage_root must identify a capture directory")

    def authorize_start(self) -> None:
        self.validate()
        if not self.enabled:
            raise PermissionError("screen capture is disabled by policy")
