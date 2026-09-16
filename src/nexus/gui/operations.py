from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from nexus.automation.planner import plan_actions
from nexus.automation.rules import evaluate_rules
from nexus.doctor import overall_status, run_checks
from nexus.reporting import snapshot_to_json
from nexus.sensors.system import collect_snapshot
from nexus.services.audit import read_audit_entries


class OperationsPage(QFrame):
    """GUI command center for the non-mutating NEXUS CLI operations."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("detailPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 24)
        layout.setSpacing(14)

        heading = QVBoxLayout()
        title = QLabel("Command Center")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Run NEXUS CLI operations without leaving the desktop interface")
        subtitle.setObjectName("subtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        layout.addLayout(heading)

        grid = QGridLayout()
        grid.setSpacing(12)
        actions = (
            ("System Status", "nexus status", self.show_status),
            ("System Doctor", "nexus doctor", self.show_doctor),
            ("Automation Plan", "nexus automate", self.show_automation),
            ("Health Report", "nexus report", self.save_report),
            ("Action History", "nexus history", self.show_history),
        )
        for index, (title_text, command, callback) in enumerate(actions):
            card = QFrame()
            card.setObjectName("panel")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            label = QLabel(title_text)
            label.setStyleSheet("font-size: 14px; font-weight: 750;")
            command_label = QLabel(command)
            command_label.setObjectName("subtitle")
            button = QPushButton("Run")
            button.setObjectName("secondaryButton")
            button.clicked.connect(callback)
            card_layout.addWidget(label)
            card_layout.addWidget(command_label)
            card_layout.addStretch()
            card_layout.addWidget(button)
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)

        output_frame = QFrame()
        output_frame.setObjectName("panel")
        output_layout = QVBoxLayout(output_frame)
        output_header = QHBoxLayout()
        output_title = QLabel("Command Output")
        output_title.setStyleSheet("font-size: 15px; font-weight: 750;")
        output_header.addWidget(output_title)
        output_header.addStretch()
        clear = QPushButton("Clear")
        clear.setObjectName("secondaryButton")
        clear.clicked.connect(lambda: self.output.clear())
        output_header.addWidget(clear)
        output_layout.addLayout(output_header)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("detailOutput")
        self.output.setPlaceholderText("Select an operation above…")
        output_layout.addWidget(self.output)
        layout.addWidget(output_frame, 1)

    def show_status(self) -> None:
        snapshot = collect_snapshot()
        self.output.setPlainText(
            "NEXUS status\n\n"
            f"Platform: {snapshot.platform}\n"
            f"Kernel:   {snapshot.kernel}\n"
            f"Host:     {snapshot.hostname}\n"
            f"CPU:      {snapshot.cpu.load_percent:.1f}% load / {snapshot.cpu.logical_cores} cores\n"
            f"Memory:   {snapshot.memory.used_percent:.1f}% used\n"
            f"Disk:     {snapshot.disk.used_percent:.1f}% used ({snapshot.disk.path})\n"
            f"Network:  {len(snapshot.network)} interface(s)\n"
            "\nRead-only operation. No system changes were made."
        )

    def show_doctor(self) -> None:
        snapshot = collect_snapshot()
        checks = run_checks(snapshot)
        status = overall_status(checks)
        lines = [f"NEXUS doctor — overall status: {status.upper()}", ""]
        lines.extend(f"[{check.status.upper():4}] {check.name}: {check.detail}" for check in checks)
        lines.append("\nRead-only operation. No system changes were made.")
        self.output.setPlainText("\n".join(lines))

    def show_automation(self) -> None:
        snapshot = collect_snapshot()
        results = evaluate_rules(snapshot)
        proposals = plan_actions(results)
        lines = ["NEXUS automation plan (dry-run)", ""]
        lines.extend(
            f"[{('TRIGGER' if result.triggered else 'OK'):7}] {result.rule}: {result.message}"
            for result in results
        )
        if proposals:
            lines.extend(("", "Action proposals:") for _ in [0])
            for proposal in proposals:
                confirmation = "yes" if proposal.requires_confirmation else "no"
                lines.extend(
                    (
                        f"- {proposal.action_id}: {proposal.action}",
                        f"  Risk: {proposal.risk} | Confirmation required: {confirmation}",
                        f"  Rationale: {proposal.rationale}",
                    )
                )
        else:
            lines.extend(("", "No automation proposals are currently triggered."))
        lines.append("No actions were executed. This operation is observation-only.")
        self.output.setPlainText("\n".join(lines))

    def save_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save NEXUS health report",
            str(Path.cwd() / "nexus-report.json"),
            "JSON files (*.json)",
        )
        if not path:
            return
        snapshot = collect_snapshot()
        Path(path).write_text(snapshot_to_json(snapshot), encoding="utf-8")
        self.output.setPlainText(f"NEXUS report\n\nReport written to:\n{path}\n\nNo system changes were made.")

    def show_history(self) -> None:
        entries = read_audit_entries(Path(".nexus/audit.jsonl"), limit=50)
        if not entries:
            self.output.setPlainText("NEXUS history\n\nNo service action audit entries found.")
            return
        lines = ["NEXUS action history — last 50", ""]
        for entry in entries:
            status = entry.result
            if entry.return_code is not None:
                status = f"{status} (exit {entry.return_code})"
            lines.append(f"{entry.timestamp} | {entry.action} | {entry.service} | {entry.risk} | {status}")
        self.output.setPlainText("\n".join(lines))
