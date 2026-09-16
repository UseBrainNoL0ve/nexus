import argparse
import json

from nexus.diagnostics.engine import collect_diagnostics
from nexus.diagnostics.incidents import build_incidents
from nexus.diagnostics.remediation import build_remediation_plan
from nexus.sensors.system import collect_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-diagnose",
        description="Analyze current Linux health signals without changing the system",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    snapshot = collect_snapshot()
    findings, errors = collect_diagnostics(snapshot)
    incidents = build_incidents(findings)
    remediation = build_remediation_plan(findings)

    if args.json:
        print(json.dumps({
            "finding_count": len(findings),
            "findings": [finding.to_dict() for finding in findings],
            "incident_count": len(incidents),
            "incidents": [incident.to_dict() for incident in incidents],
            "remediation_steps": [step.to_dict() for step in remediation],
            "collection_errors": errors,
            "read_only": True,
        }, indent=2, sort_keys=True))
        return 0

    print("NEXUS diagnostics (read-only)")
    if not findings:
        print("No actionable findings detected from the available health signals.")
    else:
        print(f"Findings: {len(findings)}")
        for finding in findings:
            confirmation = "yes" if finding.requires_confirmation else "no"
            print(f"[{finding.severity.upper():8}] {finding.title}")
            print(f"  Evidence:       {finding.evidence}")
            print(f"  Recommendation: {finding.recommendation}")
            print(f"  Confirmation:   {confirmation}")

    print()
    print(f"Incidents: {len(incidents)}")
    for incident in incidents:
        print(f"  - {incident.id}: {incident.title}")
        print(f"    Summary: {incident.summary}")

    print()
    print("Remediation proposals (not executed):")
    if not remediation:
        print("  - none")
    for step in remediation:
        confirmation = "yes" if step.requires_confirmation else "no"
        print(f"  - {step.action}")
        print(f"    Risk: {step.risk} | Confirmation required: {confirmation}")
        print(f"    Reason: {step.reason}")
        if step.command:
            print(f"    Proposed command: {step.command}")

    if errors:
        print("Collection warnings:")
        for error in errors:
            print(f"  - {error}")

    print("No actions were executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
