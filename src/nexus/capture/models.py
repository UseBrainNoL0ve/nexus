from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class CaptureState(StrEnum):
    OFF = "off"
    STARTING = "starting"
    RECORDING = "recording"
    PAUSED = "paused"
    STOPPING = "stopping"


@dataclass(frozen=True)
class CaptureSession:
    """Metadata for one local screen-capture session."""

    session_id: str
    state: CaptureState
    started_at: str
    storage_path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "started_at": self.started_at,
            "storage_path": str(self.storage_path),
        }
