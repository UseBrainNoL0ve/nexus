from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from nexus.diagnostics.engine import DiagnosticFinding


@dataclass(frozen=True)
class Incident:
    id: str
    severity: str
    category: str
    title: str
    findings: tuple[str, ...]
    evidence: tuple[str, ...]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _incident_id(category: str, findings: list[DiagnosticFinding]) -> str:
    primary = findings[0].id if findings else "unknown"
    return f"incident:{category}:{primary}"


def build_incidents(findings: list[DiagnosticFinding]) -> list[Incident]:
    """Group related diagnostic findings without executing or mutating anything."""
    grouped: dict[str, list[DiagnosticFinding]] = {}
    for finding in findings:
        grouped.setdefault(finding.category, []).append(finding)

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    incidents: list[Incident] = []
    for category, category_findings in grouped.items():
        category_findings.sort(key=lambda item: (severity_order.get(item.severity, 99), item.id))
        primary = category_findings[0]
        incidents.append(
            Incident(
                id=_incident_id(category, category_findings),
                severity=primary.severity,
                category=category,
                title=primary.title,
                findings=tuple(item.id for item in category_findings),
                evidence=tuple(item.evidence for item in category_findings),
                summary=f"{len(category_findings)} related {category} finding(s) require review.",
            )
        )

    return sorted(incidents, key=lambda item: (severity_order.get(item.severity, 99), item.id))
