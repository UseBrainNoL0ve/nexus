from __future__ import annotations

import json
from pathlib import Path

from nexus.scheduler.models import ScheduledJob


class ScheduleStore:
    """Small JSON-backed store for user-owned NEXUS schedules."""

    def __init__(self, path: Path = Path(".nexus/schedules.json")) -> None:
        self.path = path

    def load(self) -> list[ScheduledJob]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [ScheduledJob.from_dict(item) for item in payload.get("jobs", [])]

    def save(self, jobs: list[ScheduledJob]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "jobs": [job.to_dict() for job in jobs]}
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def add(self, job: ScheduledJob) -> None:
        jobs = [item for item in self.load() if item.name != job.name]
        jobs.append(job)
        self.save(jobs)

    def remove(self, name: str) -> bool:
        jobs = self.load()
        remaining = [item for item in jobs if item.name != name]
        if len(remaining) == len(jobs):
            return False
        self.save(remaining)
        return True

    def update(self, job: ScheduledJob) -> None:
        jobs = self.load()
        for index, item in enumerate(jobs):
            if item.name == job.name:
                jobs[index] = job
                self.save(jobs)
                return
        raise KeyError(job.name)
