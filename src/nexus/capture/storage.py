from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from nexus.capture.models import CaptureSession, CaptureState


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _metadata_path(root: Path) -> Path:
    return root / "sessions.jsonl"


def list_sessions(root: Path) -> list[CaptureSession]:
    path = _metadata_path(root)
    if not path.exists():
        return []
    sessions: list[CaptureSession] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        sessions.append(
            CaptureSession(
                session_id=item["session_id"],
                state=CaptureState(item["state"]),
                started_at=item["started_at"],
                storage_path=Path(item["storage_path"]),
            )
        )
    return sessions


def append_session(root: Path, session: CaptureSession) -> None:
    root.mkdir(parents=True, exist_ok=True)
    metadata = _metadata_path(root)
    metadata.touch(exist_ok=True, mode=0o600)
    with metadata.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(session.to_dict(), sort_keys=True) + "\n")
    metadata.chmod(0o600)


def new_session(root: Path, session_id: str) -> CaptureSession:
    session_dir = root / session_id
    session_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    return CaptureSession(session_id, CaptureState.STARTING, _now(), session_dir)
