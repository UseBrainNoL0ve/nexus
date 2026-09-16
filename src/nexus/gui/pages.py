from __future__ import annotations

import json
from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from nexus.doctor import overall_status, run_checks
from nexus.packages.pacman import inspect_updates
from nexus.scheduler.audit import read_entries
from nexus.scheduler.store import ScheduleStore
from nexus.sensors.system import collect_snapshot
from nexus.services.systemd import inspect_services


Loader = Callable[[], str]


class DetailPage(QFrame):
    """Reusable read-only detail page for NEXUS GUI sections."""

    def __init__(self, title: str, subtitle: str, loader: Loader) -> None:
        super().__init__()
        self.setObjectName("detailPage")
        self.loader = loader

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 24)
        layout.setSpacing(14)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("subtitle")
        heading.addWidget(title_label)
        heading.addWidget(subtitle_label)
        header.addLayout(heading)
        header.addStretch()
        refresh = QPushButton("Refresh")
        refresh.setObjectName("primaryButton")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        layout.addLayout(header)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("detailOutput")
        panel_layout.addWidget(self.output)
        layout.addWidget(panel)

        self.refresh()

    def refresh(self) -> None:
        try:
            self.output.setPlainText(self.loader())
        except Exception as exc:
            self.output.setPlainText(f"NEXUS could not load this view.\n\n{exc}")


def services_text() -> str:
    services = inspect_services()
    if not services:
        return "No systemd services were returned."
    lines = [f"{len(services)} services discovered", ""]
    for service in services:
        marker = "FAILED" if service.active_state == "failed" else service.active_state.upper()
        lines.append(f"{marker:8}  {service.unit}")
    return "\n".join(lines)


def packages_text() -> str:
    updates = inspect_updates()
    if not updates:
        return "System is up to date according to pacman."
    lines = [f"{len(updates)} package update(s) available", ""]
    for update in updates:
        lines.append(f"{update.name}  {update.current_version} -> {update.new_version}")
    return "\n".join(lines)


def doctor_text() -> str:
    snapshot = collect_snapshot()
    checks = run_checks(snapshot)
    status = overall_status(checks)
    lines = [f"Overall status: {status.upper()}", ""]
    for check in checks:
        lines.append(f"[{check.status.upper():4}] {check.name}: {check.detail}")
    return "\n".join(lines)


def scheduler_text() -> str:
    jobs = ScheduleStore().load()
    if not jobs:
        return "No scheduled jobs configured."
    rows = [f"{len(jobs)} scheduled job(s)", ""]
    for job in jobs:
        state = "enabled" if job.enabled else "disabled"
        last = job.last_run or "never"
        rows.append(f"{job.name}  |  {job.action}  |  every {job.interval_seconds}s  |  {state}  |  last: {last}")
    return "\n".join(rows)


def history_text() -> str:
    entries = read_entries(limit=50)
    if not entries:
        return "No scheduler audit entries found."
    return "\n".join(
        f"{entry.timestamp}  [{('OK' if entry.success else 'FAIL')}]  {entry.job}  |  {entry.action}  |  {entry.message}"
        for entry in entries
    )
