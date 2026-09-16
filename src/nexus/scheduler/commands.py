from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from nexus.doctor import overall_status, run_checks
from nexus.packages.pacman import inspect_updates
from nexus.scheduler.audit import read_entries
from nexus.scheduler.engine import Scheduler
from nexus.scheduler.models import ScheduledJob
from nexus.scheduler.store import ScheduleStore
from nexus.sensors.system import collect_snapshot

DEFAULT_STORE = Path(".nexus/schedules.json")
ALLOWED_ACTIONS = ("doctor", "packages")


def _run_action(action: str) -> tuple[bool, str]:
    if action == "doctor":
        status = overall_status(run_checks(collect_snapshot()))
        return status == "healthy", f"System health: {status}"
    if action == "packages":
        updates = inspect_updates()
        return True, f"Package inspection: {len(updates)} update(s) available"
    return False, f"Unknown scheduled action: {action}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-scheduler",
        description="NEXUS recurring task scheduler",
    )
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="create or replace a recurring job")
    add.add_argument("name")
    add.add_argument("--action", choices=ALLOWED_ACTIONS, required=True)
    add.add_argument("--every", type=int, required=True, metavar="SECONDS")
    add.add_argument("--no-notify", action="store_true")

    list_cmd = sub.add_parser("list", help="list configured jobs")
    list_cmd.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    remove = sub.add_parser("remove", help="remove a job")
    remove.add_argument("name")

    run = sub.add_parser("run", help="run due jobs once")
    run.add_argument("--daemon", action="store_true", help="keep checking every 5 seconds")
    run.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    history = sub.add_parser("history", help="show recent scheduler executions")
    history.add_argument("--limit", type=int, default=20)
    history.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def _print_jobs(store: ScheduleStore, json_output: bool = False) -> int:
    jobs = store.load()
    if json_output:
        print(json.dumps([job.to_dict() for job in jobs], indent=2, sort_keys=True))
        return 0
    if not jobs:
        print("No scheduled jobs configured.")
        return 0
    for job in jobs:
        state = "enabled" if job.enabled else "disabled"
        notification = "notify" if job.notify else "silent"
        last_run = job.last_run or "never"
        print(f"{job.name} | {job.action} | every {job.interval_seconds}s | {state} | {notification} | last: {last_run}")
    return 0


def _print_history(limit: int, json_output: bool = False) -> int:
    entries = read_entries(limit=limit)
    if json_output:
        print(json.dumps([entry.__dict__ for entry in entries], indent=2, sort_keys=True))
        return 0
    print(f"NEXUS scheduler history (last {limit})")
    if not entries:
        print("No scheduler audit entries found.")
        return 0
    for entry in entries:
        status = "OK" if entry.success else "FAIL"
        print(f"{entry.timestamp} | [{status}] {entry.job} | {entry.action} | {entry.message}")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    store = ScheduleStore(args.store)

    if args.command == "add":
        job = ScheduledJob(
            name=args.name,
            action=args.action,
            interval_seconds=args.every,
            notify=not args.no_notify,
        )
        store.add(job)
        print(f"Scheduled: {job.name} -> {job.action} every {job.interval_seconds}s")
        return 0

    if args.command == "list":
        return _print_jobs(store, args.json)

    if args.command == "remove":
        if not store.remove(args.name):
            print(f"Job not found: {args.name}")
            return 1
        print(f"Removed: {args.name}")
        return 0

    if args.command == "history":
        if args.limit < 1:
            print("History limit must be at least 1.")
            return 2
        return _print_history(args.limit, args.json)

    scheduler = Scheduler(store=store, action_runner=_run_action)
    if args.daemon:
        if args.json:
            print("Error: --json cannot be combined with --daemon.")
            return 2
        print("NEXUS scheduler daemon started. Press Ctrl+C to stop.")
        try:
            while True:
                scheduler.run_due()
                time.sleep(5)
        except KeyboardInterrupt:
            print("NEXUS scheduler daemon stopped.")
            return 0

    results = scheduler.run_due()
    if args.json:
        print(json.dumps([
            {
                "job": job.name,
                "action": job.action,
                "success": success,
                "message": message,
                "last_run": job.last_run,
            }
            for job, success, message in results
        ], indent=2, sort_keys=True))
        return 0 if all(success for _, success, _ in results) else 1

    if not results:
        print("No scheduled jobs are due.")
        return 0
    for job, success, message in results:
        status = "OK" if success else "FAIL"
        print(f"[{status}] {job.name}: {message}")
    return 0 if all(success for _, success, _ in results) else 1
