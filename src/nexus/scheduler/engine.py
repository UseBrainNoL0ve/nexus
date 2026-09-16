from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from nexus.scheduler.models import ScheduledJob
from nexus.scheduler.notifications import notify
from nexus.scheduler.store import ScheduleStore


ActionRunner = Callable[[str], tuple[bool, str]]
Notifier = Callable[[str, str], bool]


class Scheduler:
    """Evaluate due NEXUS jobs without executing arbitrary shell commands."""

    def __init__(
        self,
        store: ScheduleStore | None = None,
        action_runner: ActionRunner | None = None,
        notifier: Notifier | None = None,
    ) -> None:
        self.store = store or ScheduleStore()
        self.action_runner = action_runner or (lambda action: (False, f"No runner for {action}"))
        self.notifier = notifier or notify

    def run_due(self, now: datetime | None = None) -> list[tuple[ScheduledJob, bool, str]]:
        current = now or datetime.now(timezone.utc)
        results: list[tuple[ScheduledJob, bool, str]] = []
        for job in self.store.load():
            if not job.due(current):
                continue
            success, message = self.action_runner(job.action)
            updated = job.mark_run(current)
            self.store.update(updated)
            results.append((updated, success, message))
            if job.notify:
                title = f"NEXUS: {job.name}"
                self.notifier(title, message)
        return results
