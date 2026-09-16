from dataclasses import asdict, dataclass
from typing import Any

from nexus.doctor import run_checks
from nexus.core.models import SystemSnapshot
from nexus.packages.pacman import PackageManagerError, inspect_updates
from nexus.services.systemd import ServiceSnapshot, SystemdError, inspect_services


@dataclass(frozen=True)
class DiagnosticFinding:
    id: str
    category: str
    severity: str
    title: str
    evidence: str
    recommendation: str
    requires_confirmation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _doctor_findings(snapshot: SystemSnapshot) -> list[DiagnosticFinding]:
    findings: list[DiagnosticFinding] = []
    for check in run_checks(snapshot):
        if check.status != "warn":
            continue
        if check.name == "memory":
            findings.append(DiagnosticFinding(
                id="memory-pressure",
                category="resource",
                severity="warning",
                title="Memory pressure is elevated",
                evidence=check.detail,
                recommendation="Inspect memory-heavy processes and consider closing unused workloads before system pressure increases.",
            ))
        elif check.name == "disk":
            findings.append(DiagnosticFinding(
                id="disk-pressure",
                category="storage",
                severity="warning",
                title="Root filesystem usage is high",
                evidence=check.detail,
                recommendation="Review large files, caches, and package artifacts before the filesystem becomes constrained.",
            ))
        elif check.name == "network":
            findings.append(DiagnosticFinding(
                id="no-network-interface",
                category="network",
                severity="warning",
                title="No network interfaces were detected",
                evidence=check.detail,
                recommendation="Verify that the expected network adapter and connection manager are available.",
            ))
        else:
            findings.append(DiagnosticFinding(
                id=f"doctor-{check.name}",
                category="health",
                severity="warning",
                title=f"Health check requires attention: {check.name}",
                evidence=check.detail,
                recommendation="Review the reported condition before attempting any system change.",
            ))
    return findings


def _service_findings(services: list[ServiceSnapshot]) -> list[DiagnosticFinding]:
    findings: list[DiagnosticFinding] = []
    for service in services:
        if service.active_state != "failed":
            continue
        findings.append(DiagnosticFinding(
            id=f"failed-service:{service.unit}",
            category="service",
            severity="warning",
            title=f"Systemd service is failed: {service.unit}",
            evidence=f"active={service.active_state}, sub={service.sub_state}; {service.description}".strip(),
            recommendation=f"Inspect {service.unit} logs and dependencies before considering a restart or other service action.",
        ))
    return findings


def _package_findings(update_count: int) -> list[DiagnosticFinding]:
    if update_count == 0:
        return []
    return [DiagnosticFinding(
        id="package-updates-available",
        category="packages",
        severity="info",
        title="Package updates are available",
        evidence=f"pacman reports {update_count} available update(s).",
        recommendation="Review the package update plan before explicitly authorizing any package changes.",
        requires_confirmation=True,
    )]


def diagnose_system(
    snapshot: SystemSnapshot,
    services: list[ServiceSnapshot] | None = None,
    update_count: int | None = None,
) -> list[DiagnosticFinding]:
    """Build deterministic, non-executing findings from current system state."""
    findings = _doctor_findings(snapshot)

    if services is not None:
        findings.extend(_service_findings(services))

    if update_count is not None:
        findings.extend(_package_findings(update_count))

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    return sorted(findings, key=lambda item: (severity_order.get(item.severity, 99), item.id))


def collect_diagnostics(snapshot: SystemSnapshot) -> tuple[list[DiagnosticFinding], list[str]]:
    """Collect optional systemd/pacman evidence without failing the whole diagnosis."""
    findings: list[DiagnosticFinding] = []
    errors: list[str] = []

    try:
        services = inspect_services()
        findings.extend(_service_findings(services))
    except SystemdError as exc:
        errors.append(f"systemd inspection unavailable: {exc}")

    try:
        updates = inspect_updates()
        findings.extend(_package_findings(len(updates)))
    except PackageManagerError as exc:
        errors.append(f"package inspection unavailable: {exc}")

    findings = _doctor_findings(snapshot) + findings
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda item: (severity_order.get(item.severity, 99), item.id))
    return findings, errors
