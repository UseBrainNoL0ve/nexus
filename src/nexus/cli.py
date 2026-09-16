import argparse
import json
from pathlib import Path

from nexus.automation.planner import plan_actions
from nexus.automation.rules import evaluate_rules
from nexus.core.models import SystemSnapshot
from nexus.diagnostics.engine import collect_diagnostics
from nexus.diagnostics.incidents import build_incidents
from nexus.diagnostics.remediation import build_remediation_plan
from nexus.doctor import checks_to_dict, overall_status, run_checks
from nexus.packages.actions import plan_package_updates
from nexus.packages.engine import execute_package_update
from nexus.packages.pacman import PackageManagerError, inspect_updates
from nexus.reporting import snapshot_to_json
from nexus.sensors.system import collect_snapshot
from nexus.services.actions import plan_service_action
from nexus.services.audit import read_audit_entries
from nexus.services.engine import execute_service_action
from nexus.services.systemd import SystemdError, inspect_services


AUDIT_PATH = Path(".nexus/audit.jsonl")


def _print_status(snapshot: SystemSnapshot, json_output: bool = False) -> None:
    if json_output:
        payload = snapshot.to_dict()
        payload["read_only"] = True
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print(f"NEXUS {snapshot.platform} / {snapshot.kernel}")
    print(f"Host:    {snapshot.hostname}")
    print(f"CPU:     {snapshot.cpu.load_percent:.1f}% load / {snapshot.cpu.logical_cores} cores")
    print(f"Memory:  {snapshot.memory.used_percent:.1f}% used")
    print(f"Disk:    {snapshot.disk.used_percent:.1f}% used ({snapshot.disk.path})")
    print(f"Network: {len(snapshot.network)} interface(s)")


def _print_doctor(snapshot: SystemSnapshot, json_output: bool = False) -> int:
    checks = run_checks(snapshot)
    status = overall_status(checks)

    if json_output:
        print(
            json.dumps(
                {
                    "status": status,
                    "checks": checks_to_dict(checks),
                    "read_only": True,
                },
                indent=2,
            )
        )
        return 1 if status == "warn" else 0

    for check in checks:
        print(f"[{check.status.upper():4}] {check.name}: {check.detail}")
    return 1 if status == "warn" else 0


def _print_diagnose(snapshot: SystemSnapshot, json_output: bool = False) -> int:
    findings, errors = collect_diagnostics(snapshot)
    incidents = build_incidents(findings)
    remediation = build_remediation_plan(findings)
    warning_count = sum(1 for finding in findings if finding.severity in {"warning", "critical"})

    if json_output:
        print(
            json.dumps(
                {
                    "finding_count": len(findings),
                    "findings": [finding.to_dict() for finding in findings],
                    "incident_count": len(incidents),
                    "incidents": [incident.to_dict() for incident in incidents],
                    "remediation_steps": [step.to_dict() for step in remediation],
                    "collection_errors": errors,
                    "read_only": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1 if warning_count else 0

    print("NEXUS diagnosis (read-only)")
    if not findings:
        print("System signals look normal from the available evidence.")
        if errors:
            print(f"Collection warnings: {len(errors)}")
        print("No actions were executed.")
        return 0

    print(f"Findings: {len(findings)}")
    for finding in findings:
        print()
        print(f"[{finding.severity.upper():8}] {finding.title}")
        print(f"  Why it matters: {finding.evidence}")
        print(f"  Next step:      {finding.recommendation}")
        print(f"  Confirmation:   {'yes' if finding.requires_confirmation else 'no'}")

    print()
    print(f"Incidents: {len(incidents)}")
    for incident in incidents:
        print(f"  - {incident.id}: {incident.title}")
        print(f"    {incident.summary}")

    print()
    print("Suggested remediation (not executed):")
    if not remediation:
        print("  - none")
    for step in remediation:
        print(f"  - {step.action}")
        print(f"    Risk: {step.risk} | Confirmation required: {'yes' if step.requires_confirmation else 'no'}")
        print(f"    Reason: {step.reason}")
        if step.command:
            print(f"    Proposed command: {step.command}")

    if errors:
        print()
        print("Collection warnings:")
        for error in errors:
            print(f"  - {error}")

    print()
    print("No actions were executed. Review the evidence before approving any mutation.")
    return 1 if warning_count else 0


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


def _print_services(json_output: bool = False) -> int:
    try:
        services = inspect_services()
    except SystemdError as exc:
        if json_output:
            print(
                json.dumps(
                    {
                        "service_manager": "systemd",
                        "services": [],
                        "count": 0,
                        "read_only": True,
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print("NEXUS system services (read-only)")
            print(f"Systemd inspection failed: {exc}")
        return 1

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

    if json_output:
        print(
            json.dumps(
                {
                    "service_manager": "systemd",
                    "services": [
                        {
                            "unit": service.unit,
                            "load_state": service.load_state,
                            "active_state": service.active_state,
                            "sub_state": service.sub_state,
                            "description": service.description,
                            "enabled_state": service.enabled_state,
                        }
                        for service in services
                    ],
                    "count": len(services),
                    "summary": {
                        "running": len(running),
                        "failed": len(failed),
                        "stopped": len(stopped),
                        "enabled": len(enabled),
                    },
                    "read_only": True,
                },
                indent=2,
            )
        )
        return 0

    print("NEXUS system services (read-only)")

    if not services:
        print("No service units were found.")
        return 0

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


def _inspect_packages(json_output: bool = False) -> tuple[int, list]:
    try:
        updates = inspect_updates()
    except PackageManagerError as exc:
        if json_output:
            print(
                json.dumps(
                    {
                        "package_manager": "pacman",
                        "updates": [],
                        "count": 0,
                        "read_only": True,
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print("NEXUS package updates (read-only)")
            print(f"Package inspection failed: {exc}")
        return 1, []

    if json_output:
        print(
            json.dumps(
                {
                    "package_manager": "pacman",
                    "updates": [
                        {
                            "repository": update.repository,
                            "name": update.name,
                            "current_version": update.current_version,
                            "available_version": update.available_version,
                        }
                        for update in updates
                    ],
                    "count": len(updates),
                    "read_only": True,
                },
                indent=2,
            )
        )
        return 0, updates

    print("NEXUS package updates (read-only)")

    if not updates:
        print("No pending package updates reported by pacman.")
        return 0, []

    print(f"Updates: {len(updates)}")
    for update in updates:
        print(
            f"  - {update.repository}/{update.name}: "
            f"{update.current_version} -> {update.available_version}"
        )
    print("No packages were changed.")
    return 0, updates


def _plan_package_updates(confirm: bool) -> int:
    print("NEXUS package update plan")
    code, updates = _inspect_packages()
    if code != 0:
        return code
    if not updates:
        return 0

    proposals = plan_package_updates(updates)
    print("Action proposals:")
    for proposal in proposals:
        print(f"  - {proposal.repository}/{proposal.package}")
        print(f"    {proposal.current_version} -> {proposal.available_version}")
        print(f"    Risk: {proposal.risk} | Confirmation required: yes")
        print(f"    Command: {' '.join(proposal.command)}")

    if not confirm:
        print("No packages were changed. Use --confirm only after reviewing the plan.")
        return 0

    print("Executing confirmed package update plan...")
    failures = 0
    for proposal in proposals:
        result = execute_package_update(proposal, confirmed=True)
        if result.return_code == 0:
            print(f"  OK  {proposal.repository}/{proposal.package}")
            continue

        failures += 1
        print(f"  FAIL {proposal.repository}/{proposal.package}")
        if result.return_code is not None:
            print(f"       return code: {result.return_code}")
        if result.stderr:
            print(f"       error: {result.stderr.strip()}")

    return 1 if failures else 0


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

    status = sub.add_parser("status", help="show a system snapshot")
    status.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output",
    )

    doctor = sub.add_parser("doctor", help="run non-destructive health checks")
    doctor.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output",
    )
    diagnose = sub.add_parser(
        "diagnose",
        help="explain what needs attention and propose safe next steps",
    )
    diagnose.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output",
    )
    sub.add_parser("automate", help="evaluate automation rules in dry-run mode")

    services = sub.add_parser("services", help="inspect systemd services without modifying them")
    services.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output",
    )

    packages = sub.add_parser("packages", help="inspect or plan pacman updates")
    packages.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON output",
    )
    package_actions = packages.add_subparsers(dest="package_action")
    update = package_actions.add_parser(
        "update",
        help="plan available package updates without modifying packages",
    )
    update.add_argument(
        "--confirm",
        action="store_true",
        help="explicitly authorize execution of the reviewed package update plan",
    )

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

    if args.command == "status":
        snapshot = collect_snapshot()
        _print_status(snapshot, args.json)
        return 0

    if args.command == "services":
        return _print_services(args.json)

    if args.command == "packages":
        if args.package_action == "update":
            if args.json:
                print("Error: --json is only supported for package inspection.")
                return 2
            return _plan_package_updates(args.confirm)
        return _inspect_packages(args.json)[0]

    if args.command == "service":
        return _print_service_action(args.service, args.action, args.dry_run, args.confirm)

    if args.command == "history":
        if args.limit < 1:
            print("History limit must be at least 1.")
            return 2
        return _print_history(args.limit)

    snapshot = collect_snapshot()

    if args.command == "doctor":
        return _print_doctor(snapshot, args.json)

    if args.command == "diagnose":
        return _print_diagnose(snapshot, args.json)

    if args.command == "automate":
        _print_automation(snapshot)
        return 0

    if args.command == "report":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(snapshot_to_json(snapshot), encoding="utf-8")
        print(f"Report written to {args.output}")
        return 0

    return 2
