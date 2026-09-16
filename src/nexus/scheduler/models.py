from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class ScheduledJob:
    """A persisted, recurring NEXUS task."""

    name: str
    action: str
    interval_seconds: int
    notify: bool = True
    enabled: bool = True
    last_run: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Job name must not be empty")
        if self.interval_seconds < 1:
            raise ValueError("Interval must be at least 1 second")

    def due(self, now: datetime | None = None) -> bool:
        if not self.enabled:
            return False
        if self.last_run is None:
            return True
        current = now or datetime.now(timezone.utc)
        previous = datetime.fromisoformat(self.last_run)
        return current >= previous + timedelta(seconds=self.interval_seconds)

    def mark_run(self, when: datetime | None = None) -> "ScheduledJob":
        current = when or datetime.now(timezone.utc)
        return ScheduledJob(
            name=self.name,
            action=self.action,
            interval_seconds=self.interval_seconds,
            notify=self.notify,
            enabled=self.enabled,
            last_run=current.isoformat(),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "ScheduledJob":
        return cls(
            name=str(payload["name"]),
            action=str(payload["action"]),
            interval_seconds=int(payload["interval_seconds"]),
            notify=bool(payload.get("notify", True)),
            enabled=bool(payload.get("enabled", True)),
            last_run=payload.get("last_run"),
        )
