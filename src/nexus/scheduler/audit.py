from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


DEFAULT_AUDIT_PATH = Path(".nexus/scheduler-audit.jsonl")


@dataclass(frozen=True)
class SchedulerAuditEntry:
    timestamp: str
    job: str
    action: str
    success: bool
    message: str


def write_entry(entry: SchedulerAuditEntry, path: Path = DEFAULT_AUDIT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), sort_keys=True) + "\n")


def new_entry(*, job: str, action: str, success: bool, message: str, timestamp: datetime | None = None) -> SchedulerAuditEntry:
    current = timestamp or datetime.now(timezone.utc)
    return SchedulerAuditEntry(
        timestamp=current.isoformat(),
        job=job,
        action=action,
        success=success,
        message=message,
    )


def read_entries(path: Path = DEFAULT_AUDIT_PATH, *, limit: int = 20) -> list[SchedulerAuditEntry]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if not path.exists():
        return []
    entries: list[SchedulerAuditEntry] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                entries.append(SchedulerAuditEntry(**json.loads(line)))
    return entries[-limit:]
