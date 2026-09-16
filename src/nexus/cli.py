import argparse
from pathlib import Path

from nexus.automation.planner import plan_actions
from nexus.automation.rules import evaluate_rules
from nexus.core.models import SystemSnapshot
from nexus.doctor import run_checks
from nexus.reporting import snapshot_to_json
from nexus.sensors.system import collect_snapshot


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexus", description="Linux system intelligence CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show a system snapshot")
    sub.add_parser("doctor", help="run non-destructive health checks")
    sub.add_parser("automate", help="evaluate automation rules in dry-run mode")
    report = sub.add_parser("report", help="write a JSON health report")
    report.add_argument("--output", type=Path, default=Path("nexus-report.json"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
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
