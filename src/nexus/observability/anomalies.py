from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from nexus.observability.history import Observation


@dataclass(frozen=True)
class TrendFinding:
    metric: str
    severity: str
    title: str
    evidence: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_trends(observations: list[Observation]) -> list[TrendFinding]:
    """Detect sustained resource pressure using explicit, explainable thresholds."""
    if len(observations) < 3:
        return []

    findings: list[TrendFinding] = []
    recent = observations[-3:]

    memory = [item.snapshot["memory"]["used_percent"] for item in recent]
    disk = [item.snapshot["disk"]["used_percent"] for item in recent]
    cpu = [item.snapshot["cpu"]["load_percent"] for item in recent]

    if all(value >= 90.0 for value in memory):
        findings.append(TrendFinding(
            metric="memory_used_percent",
            severity="warning",
            title="Memory pressure is persistent",
            evidence=f"The last {len(memory)} observations were all at or above 90% memory usage.",
            recommendation="Inspect memory-heavy processes and workload growth before adding more load.",
        ))

    if all(value >= 85.0 for value in disk):
        findings.append(TrendFinding(
            metric="disk_used_percent",
            severity="warning",
            title="Disk usage is persistently high",
            evidence=f"The last {len(disk)} observations were all at or above 85% root filesystem usage.",
            recommendation="Review large files, caches, logs, and package artifacts before storage becomes constrained.",
        ))

    if all(value >= 80.0 for value in cpu):
        findings.append(TrendFinding(
            metric="cpu_load_percent",
            severity="info",
            title="CPU load remains elevated",
            evidence=f"The last {len(cpu)} observations were all at or above 80% CPU load.",
            recommendation="Identify sustained CPU-heavy workloads and verify whether the load is expected.",
        ))

    metric_order = {
        "disk_used_percent": 0,
        "memory_used_percent": 1,
        "cpu_load_percent": 2,
    }
    findings.sort(key=lambda item: metric_order.get(item.metric, 99))
    return findings
