from dataclasses import asdict, dataclass
import sys
from typing import Any

from nexus.core.models import SystemSnapshot


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_checks(snapshot: SystemSnapshot) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.append(CheckResult(
        "platform",
        "ok" if snapshot.platform == "Linux" else "warn",
        f"Detected {snapshot.platform} / {snapshot.kernel}",
    ))
    checks.append(CheckResult(
        "python",
        "ok" if sys.version_info >= (3, 11) else "warn",
        f"Python {snapshot.python_version}",
    ))
    checks.append(CheckResult(
        "memory",
        "warn" if snapshot.memory.used_percent >= 90 else "ok",
        f"Memory usage {snapshot.memory.used_percent:.1f}%",
    ))
    checks.append(CheckResult(
        "disk",
        "warn" if snapshot.disk.used_percent >= 85 else "ok",
        f"Root filesystem usage {snapshot.disk.used_percent:.1f}%",
    ))
    checks.append(CheckResult(
        "network",
        "ok" if snapshot.network else "warn",
        f"Detected {len(snapshot.network)} network interface(s)",
    ))
    return checks


def checks_to_dict(checks: list[CheckResult]) -> list[dict[str, Any]]:
    return [check.to_dict() for check in checks]


def overall_status(checks: list[CheckResult]) -> str:
    statuses = {check.status for check in checks}
    if "warn" in statuses:
        return "warn"
    return "healthy"
