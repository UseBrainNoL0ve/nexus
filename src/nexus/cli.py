import argparse
from pathlib import Path

from nexus.automation.planner import plan_actions
from nexus.automation.rules import evaluate_rules
from nexus.core.models import SystemSnapshot
from nexus.doctor import run_checks
from nexus.reporting import snapshot_to_json
from nexus.sensors.system import collect_snapshot
from nexus.services.actions import plan_service_action
from nexus.services.audit import read_audit_entries
from nexus.services.engine import execute_service_action
from nexus.services.systemd import SystemdError, inspect_services


AUDIT_PATH = Path(".nexus/audit.jsonl")


def _print_status(snapshot: SystemSnapshot) -> None:
    print(f"NEXUS {snapshot.platform} / {snapshot.kernel}")
    print(f"Host:    {snapshot.hostname}")
    print(f"CPU:     {snapshot.cpu.load_percent:.1f}% load / {snapshot.cpu.logical_cores} cores")
    print(f"Memory:  {snapshot.memory.used_percent:.1f}% used")
    print(f"Disk:    {snapshot.disk.used_percent:.1f}% used ({snapshot.disk.path})")
    print(f"Network: {len(snapshot.network)} interface(s)")


def _print_automation(snapshot: SystemSnapshot) -> None:
    print("NEXUS automation plan (dry-run)")
    results = evaluate_rules(snapshot)

    for result in results:
        status = "TRIGGER" if result.triggered else "OK"
        print(f"[{status:7}] {result.rule}: {result.message}")

    proposals = plan_actions(results)
    if not proposals:
        print("No automation proposals are currently triggered.")
        return

    print("Action proposals:")
    for proposal in proposals:
        confirmation = "yes" if proposal.requires_confirmation else "no"
        print(f"  - {proposal.action_id}: {proposal.action}")
        print(f"    Risk: {proposal.risk} | Confirmation required: {confirmation}")
        print(f"    Rationale: {proposal.rationale}")

    print("No actions were executed. This command is observation-only.")


def _print_services() -> int:
    print("NEXUS system services (read-only)")

    try:
        services = inspect_services()
    except SystemdError as exc:
        print(f"Systemd inspection failed: {exc}")
        return 1

    if not services:
        print("No service units were found.")
        return 0

    running = [service for service in services if service.active_state == "active"]
    failed = [service for service in services if service.active_state == "failed"]
    stopped = [
        service
        for service in services
        if service.active_state in {"inactive", "deactivating"}
    ]
    enabled = [
        service
        for service in services
        if service.enabled_state in {"enabled", "enabled-runtime"}
    ]

    print(f"Services: {len(services)}")
    print(f"Running:  {len(running)}")
    print(f"Failed:   {len(failed)}")
    print(f"Stopped:  {len(stopped)}")
    print(f"Enabled:  {len(enabled)}")

    if failed:
        print("Failed services:")
        for service in failed:
            print(f"  - {service.unit}: {service.description}")

    return 0


def _print_service_action(service: str, action: str, dry_run: bool, confirm: bool) -> int:
    try:
        proposal = plan_service_action(service, action)
    except ValueError as exc:
        print(f"Invalid service action: {exc}")
        return 2

    print("NEXUS service action")
    print()
    print(f"Service: {proposal.service}")
    print(f"Action:  {proposal.action}")
    print(f"Risk:    {proposal.risk}")
    print(f"Command: {' '.join(proposal.command)}")
    print(f"Reason:  {proposal.rationale}")
    print()

    if dry_run:
        print("No changes were made.")
        print("Dry-run only; confirmation required before execution.")
        execute_service_action(proposal, confirmed=False, audit_path=AUDIT_PATH)
        return 0

    result = execute_service_action(
        proposal,
        confirmed=confirm,
        audit_path=AUDIT_PATH,
    )
    if not result.executed:
        print("No changes were made.")
        print("Confirmation required before execution.")
        return 0

    if result.return_code == 0:
        print("Action completed successfully.")
        return 0

    print("Action execution failed.")
    if result.return_code is not None:
        print(f"Return code: {result.return_code}")
    if result.stderr:
        print(f"Error: {result.stderr.strip()}")
    return 1


def _print_history(limit: int) -> int:
    print(f"NEXUS action history (last {limit})")
    entries = read_audit_entries(AUDIT_PATH, limit=limit)
    if not entries:
        print("No audit entries found.")
        return 0

    for entry in entries:
        status = entry.result
        if entry.return_code is not None:
            status = f"{status} (exit {entry.return_code})"
        print(f"{entry.timestamp} | {entry.action} | {entry.service} | {entry.risk} | {status}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexus", description="Linux system intelligence CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show a system snapshot")
    sub.add_parser("doctor", help="run non-destructive health checks")
    sub.add_parser("automate", help="evaluate automation rules in dry-run mode")
    sub.add_parser("services", help="inspect systemd services without modifying them")

    service = sub.add_parser("service", help="plan or execute a systemd service action")
    service.add_argument("action", choices=("start", "stop", "restart"))
    service.add_argument("service", help="systemd service unit, for example NetworkManager.service")
    service.add_argument("--dry-run", action="store_true", help="show the planned action without executing it")
    service.add_argument("--confirm", action="store_true", help="explicitly authorize execution of the planned action")

    history = sub.add_parser("history", help="show recent service action audit entries")
    history.add_argument("--limit", type=int, default=20, help="number of recent entries to show")

    report = sub.add_parser("report", help="write a JSON health report")
    report.add_argument("--output", type=Path, default=Path("nexus-report.json"))
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "services":
        return _print_services()

    if args.command == "service":
        return _print_service_action(args.service, args.action, args.dry_run, args.confirm)

    if args.command == "history":
        if args.limit < 1:
            print("History limit must be at least 1.")
            return 2
        return _print_history(args.limit)

    snapshot = collect_snapshot()

    if args.command == "status":
        _print_status(snapshot)
        return 0

    if args.command == "doctor":
        has_warnings = False
        for check in run_checks(snapshot):
            print(f"[{check.status.upper():4}] {check.name}: {check.detail}")
            has_warnings |= check.status == "warn"
        return 1 if has_warnings else 0

    if args.command == "automate":
        _print_automation(snapshot)
        return 0

    if args.command == "report":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(snapshot_to_json(snapshot), encoding="utf-8")
        print(f"Report written to {args.output}")
        return 0

    return 2
