from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass(frozen=True)
class AuditEntry:
    """A durable record of a planned or attempted service action."""

    timestamp: str
    service: str
    action: str
    risk: str
    confirmed: bool
    executed: bool
    result: str
    return_code: int | None = None


def write_audit_entry(entry: AuditEntry, path: Path) -> None:
    """Append one audit entry as JSON Lines, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), sort_keys=True) + "\n")


def read_audit_entries(path: Path, *, limit: int = 20) -> list[AuditEntry]:
    """Read the most recent audit entries from a JSON Lines log."""
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if not path.exists():
        return []

    entries: list[AuditEntry] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            entries.append(AuditEntry(**json.loads(line)))

    return entries[-limit:]


def new_audit_entry(
    *,
    service: str,
    action: str,
    risk: str,
    confirmed: bool,
    executed: bool,
    result: str,
    return_code: int | None = None,
) -> AuditEntry:
    """Create a timestamped audit entry using UTC."""
    return AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        service=service,
        action=action,
        risk=risk,
        confirmed=confirmed,
        executed=executed,
        result=result,
        return_code=return_code,
    )
