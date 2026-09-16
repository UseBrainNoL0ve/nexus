from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from nexus.scheduler.engine import Scheduler
from nexus.scheduler.models import ScheduledJob
from nexus.scheduler.store import ScheduleStore


class SchedulerTests(unittest.TestCase):
    def test_job_is_due_without_previous_run(self):
        job = ScheduledJob("doctor", "doctor", 60)
        self.assertTrue(job.due(datetime.now(timezone.utc)))

    def test_job_waits_until_interval_has_elapsed(self):
        now = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
        job = ScheduledJob("doctor", "doctor", 60, last_run=now.isoformat())
        self.assertFalse(job.due(now + timedelta(seconds=59)))
        self.assertTrue(job.due(now + timedelta(seconds=60)))

    def test_store_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ScheduleStore(Path(directory) / "schedules.json")
            job = ScheduledJob("report", "report", 300, notify=False)
            store.add(job)
            self.assertEqual(store.load(), [job])
            self.assertTrue(store.remove("report"))
            self.assertEqual(store.load(), [])

    def test_scheduler_runs_due_job_and_notifies(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ScheduleStore(Path(directory) / "schedules.json")
            store.add(ScheduledJob("doctor", "doctor", 60, notify=True))
            calls = []
            notices = []

            scheduler = Scheduler(
                store=store,
                action_runner=lambda action: (calls.append(action) or (True, "Doctor check completed")),
                notifier=lambda title, message: notices.append((title, message)) or True,
            )
            now = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
            results = scheduler.run_due(now)

            self.assertEqual(calls, ["doctor"])
            self.assertEqual(len(results), 1)
            self.assertEqual(notices, [("NEXUS: doctor", "Doctor check completed")])
            self.assertFalse(store.load()[0].due(now))


if __name__ == "__main__":
    unittest.main()
