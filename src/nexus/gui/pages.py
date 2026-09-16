from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from nexus.doctor import overall_status, run_checks
from nexus.packages.actions import plan_package_updates
from nexus.packages.engine import execute_package_update
from nexus.packages.pacman import inspect_updates
from nexus.scheduler.audit import read_entries
from nexus.scheduler.store import ScheduleStore
from nexus.sensors.system import collect_snapshot
from nexus.services.actions import plan_service_action
from nexus.services.engine import execute_service_action
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
        refresh = QPushButton("↻  Refresh")
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


class ServicesPage(QFrame):
    """Interactive systemd inventory with confirmation-gated actions."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("detailPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 24)
        layout.setSpacing(14)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("System Services")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Inspect and control individual systemd units")
        subtitle.setObjectName("subtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        refresh = QPushButton("↻  Refresh")
        refresh.setObjectName("primaryButton")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        layout.addLayout(header)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(("SERVICE", "STATE", "ENABLED", "DESCRIPTION"))
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        self.action_label = QLabel("Select a service to manage it")
        self.action_label.setObjectName("subtitle")
        actions.addWidget(self.action_label)
        actions.addStretch()
        for action in ("start", "restart", "stop"):
            button = QPushButton(action.capitalize())
            button.setObjectName("secondaryButton")
            button.clicked.connect(lambda checked=False, name=action: self.run_action(name))
            actions.addWidget(button)
        layout.addLayout(actions)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.refresh()

    def _selection_changed(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            unit = self.table.item(rows[0].row(), 0).text()
            self.action_label.setText(f"Selected: {unit}")

    def refresh(self) -> None:
        try:
            services = inspect_services()
            self.table.setRowCount(len(services))
            for row, service in enumerate(services):
                values = (service.unit, service.active_state, service.enabled_state, service.description)
                for column, value in enumerate(values):
                    self.table.setItem(row, column, QTableWidgetItem(str(value)))
            self.action_label.setText(f"{len(services)} services • select one to manage it")
        except Exception as exc:
            self.table.setRowCount(0)
            self.action_label.setText(f"Could not load services: {exc}")

    def run_action(self, action: str) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "NEXUS", "Select a service first.")
            return
        service = self.table.item(rows[0].row(), 0).text()
        proposal = plan_service_action(service, action)
        answer = QMessageBox.question(
            self,
            f"Confirm {action}",
            f"Run '{action}' for {service}?\n\nRisk: {proposal.risk}\n{proposal.rationale}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        result = execute_service_action(proposal, confirmed=True)
        if result.return_code == 0:
            QMessageBox.information(self, "NEXUS", f"{action.capitalize()} completed for {service}.")
        else:
            QMessageBox.warning(self, "NEXUS", result.stderr or f"{action.capitalize()} failed.")
        self.refresh()


class PackagesPage(QFrame):
    """Interactive package update inventory with explicit confirmation."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("detailPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 24)
        layout.setSpacing(14)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Package Updates")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Review pacman updates and apply them individually")
        subtitle.setObjectName("subtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        refresh = QPushButton("↻  Refresh")
        refresh.setObjectName("primaryButton")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        layout.addLayout(header)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(("PACKAGE", "REPOSITORY", "CURRENT", "AVAILABLE"))
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        self.action_label = QLabel("Select an update to prepare it")
        self.action_label.setObjectName("subtitle")
        actions.addWidget(self.action_label)
        actions.addStretch()
        update_button = QPushButton("Update Selected")
        update_button.setObjectName("secondaryButton")
        update_button.clicked.connect(self.update_selected)
        actions.addWidget(update_button)
        layout.addLayout(actions)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.refresh()

    def _selection_changed(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if rows:
            package = self.table.item(rows[0].row(), 0).text()
            self.action_label.setText(f"Selected: {package}")

    def refresh(self) -> None:
        try:
            updates = inspect_updates()
            self.table.setRowCount(len(updates))
            for row, update in enumerate(updates):
                values = (update.name, update.repository, update.current_version, update.available_version)
                for column, value in enumerate(values):
                    self.table.setItem(row, column, QTableWidgetItem(str(value)))
            self.action_label.setText(f"{len(updates)} updates available")
        except Exception as exc:
            self.table.setRowCount(0)
            self.action_label.setText(f"Could not inspect packages: {exc}")

    def update_selected(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "NEXUS", "Select a package update first.")
            return
        updates = inspect_updates()
        row = rows[0].row()
        if row >= len(updates):
            self.refresh()
            return
        proposal = plan_package_updates(updates)[row]
        answer = QMessageBox.question(
            self,
            "Confirm package update",
            f"Update {proposal.package}?\n\n{proposal.current_version} → {proposal.available_version}\nRepository: {proposal.repository}\n\nThis changes system packages and requires explicit confirmation.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        result = execute_package_update(proposal, confirmed=True)
        if result.return_code == 0:
            QMessageBox.information(self, "NEXUS", f"Updated {proposal.package} successfully.")
        else:
            QMessageBox.warning(self, "NEXUS", result.stderr or "Package update failed. Check your authentication setup.")
        self.refresh()


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
        lines.append(f"{update.name}  {update.current_version} -> {update.available_version}")
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
