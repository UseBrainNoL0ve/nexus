from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot

from nexus.doctor import run_checks
from nexus.packages.pacman import inspect_updates
from nexus.sensors.system import collect_snapshot
from nexus.services.systemd import inspect_services


@dataclass(frozen=True)
class DashboardData:
    snapshot: object
    checks: list[object]
    services: list[object]
    updates: list[object]


class DashboardWorker(QObject):
    """Collect dashboard telemetry away from the Qt GUI thread."""

    finished = Signal(object)
    failed = Signal(str)

    @Slot()
    def run(self) -> None:
        try:
            snapshot = collect_snapshot()
            checks = run_checks(snapshot)
            services = inspect_services()
            updates = inspect_updates()
            self.finished.emit(DashboardData(snapshot, checks, services, updates))
        except Exception as exc:
            self.failed.emit(str(exc))
