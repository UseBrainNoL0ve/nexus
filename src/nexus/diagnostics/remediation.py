from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from nexus.diagnostics.engine import DiagnosticFinding


@dataclass(frozen=True)
class RemediationStep:
    action: str
    reason: str
    risk: str
    command: str | None
    requires_confirmation: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_remediation_plan(findings: list[DiagnosticFinding]) -> list[RemediationStep]:
    """Translate findings into explainable proposals; never execute commands."""
    steps: list[RemediationStep] = []
    for finding in findings:
        if finding.id == "memory-pressure":
            steps.append(RemediationStep(
                action="Inspect memory-heavy processes",
                reason=finding.evidence,
                risk="low",
                command="ps -eo pid,comm,%mem,%cpu --sort=-%mem | head",
                requires_confirmation=False,
            ))
        elif finding.id == "disk-pressure":
            steps.append(RemediationStep(
                action="Inspect large filesystem consumers",
                reason=finding.evidence,
                risk="low",
                command="du -xhd1 / 2>/dev/null | sort -h",
                requires_confirmation=False,
            ))
        elif finding.id.startswith("failed-service:"):
            unit = finding.id.split(":", 1)[1]
            steps.append(RemediationStep(
                action=f"Inspect logs for {unit}",
                reason=finding.evidence,
                risk="low",
                command=f"journalctl -u {unit} -n 50 --no-pager",
                requires_confirmation=False,
            ))
        elif finding.id == "package-updates-available":
            steps.append(RemediationStep(
                action="Review the package update plan",
                reason=finding.evidence,
                risk="medium",
                command="pacman -Qu",
                requires_confirmation=True,
            ))
        else:
            steps.append(RemediationStep(
                action=f"Review: {finding.title}",
                reason=finding.evidence,
                risk="unknown",
                command=None,
                requires_confirmation=finding.requires_confirmation,
            ))
    return steps
