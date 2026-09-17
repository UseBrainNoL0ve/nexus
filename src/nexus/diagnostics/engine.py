from dataclasses import asdict, dataclass
from typing import Any

from nexus.doctor import run_checks
from nexus.core.models import SystemSnapshot
from nexus.packages.generic import inspect_updates
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
            findings.append(DiagnosticFinding("memory-pressure", "resource", "warning", "Memory pressure is elevated", check.detail, "Inspect memory-heavy processes and consider closing unused workloads before system pressure increases."))
        elif check.name == "disk":
            findings.append(DiagnosticFinding("disk-pressure", "storage", "warning", "Root filesystem usage is high", check.detail, "Review large files, caches, and package artifacts before the filesystem becomes constrained."))
        elif check.name == "network":
            findings.append(DiagnosticFinding("no-network-interface", "network", "warning", "No network interfaces were detected", check.detail, "Verify that the expected network adapter and connection manager are available."))
        else:
            findings.append(DiagnosticFinding(f"doctor-{check.name}", "health", "warning", f"Health check requires attention: {check.name}", check.detail, "Review the reported condition before attempting any system change."))
    return findings


def _service_findings(services: list[ServiceSnapshot]) -> list[DiagnosticFinding]:
    return [DiagnosticFinding(f"failed-service:{service.unit}", "service", "warning", f"Service is failed: {service.unit}", f"unit={service.unit}; active={service.active_state}, sub={service.sub_state}; {service.description}".strip(), f"Inspect {service.unit} logs and dependencies before considering a restart or other service action.") for service in services if service.active_state == "failed"]


def _package_findings(update_count: int) -> list[DiagnosticFinding]:
    if update_count == 0:
        return []
    return [DiagnosticFinding("package-updates-available", "packages", "info", "Package updates are available", f"Native package manager reports {update_count} available update(s).", "Review the package update plan before explicitly authorizing any package changes.", True)]


def diagnose_system(snapshot: SystemSnapshot, services: list[ServiceSnapshot] | None = None, update_count: int | None = None) -> list[DiagnosticFinding]:
    """Build deterministic, non-executing findings from current system state."""
    findings = _doctor_findings(snapshot)
    if services is not None:
        findings.extend(_service_findings(services))
    if update_count is not None:
        findings.extend(_package_findings(update_count))
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    return sorted(findings, key=lambda item: (severity_order.get(item.severity, 99), item.id))


def collect_diagnostics(snapshot: SystemSnapshot) -> tuple[list[DiagnosticFinding], list[str]]:
    """Collect optional service/package evidence without failing the whole diagnosis."""
    findings: list[DiagnosticFinding] = []
    errors: list[str] = []
    try:
        findings.extend(_service_findings(inspect_services()))
    except SystemdError as exc:
        errors.append(f"service inspection unavailable: {exc}")
    try:
        findings.extend(_package_findings(len(inspect_updates())))
    except (OSError, RuntimeError) as exc:
        errors.append(f"package inspection unavailable: {exc}")
    findings = _doctor_findings(snapshot) + findings
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda item: (severity_order.get(item.severity, 99), item.id))
    return findings, errors
