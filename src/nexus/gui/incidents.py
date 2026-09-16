from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout

from nexus.diagnostics.incidents import build_incidents
from nexus.diagnostics.remediation import build_remediation_plan
from nexus.sensors.system import collect_snapshot
from nexus.diagnostics.engine import collect_diagnostics


class IncidentCenterPage(QFrame):
    """Explainable incident view: evidence first, remediation second, execution elsewhere."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("detailPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 24)
        layout.setSpacing(12)
        title = QLabel("Incident & Remediation Center")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Investigate current findings, understand evidence, and review safe next steps")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        refresh = QPushButton("↻  Investigate Now")
        refresh.setObjectName("primaryButton")
        refresh.clicked.connect(self.refresh)
        layout.addWidget(refresh)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("detailOutput")
        layout.addWidget(self.output, 1)
        self.refresh()

    def refresh(self) -> None:
        snapshot = collect_snapshot()
        findings, errors = collect_diagnostics(snapshot)
        incidents = build_incidents(findings)
        plans = build_remediation_plan(findings)
        lines = [
            "NEXUS INVESTIGATION",
            f"Host: {snapshot.hostname}",
            f"Findings: {len(findings)} • Incidents: {len(incidents)} • Plans: {len(plans)}",
            "",
        ]
        if errors:
            lines.extend(["Collection notes:", *[f"- {error}" for error in errors], ""])
        if not incidents:
            lines.append("No active incidents detected. Current system evidence is within the configured rules.")
        else:
            lines.append("INCIDENTS")
            for incident in incidents:
                lines.extend(
                    [
                        f"[{incident.severity.upper()}] {incident.title}",
                        f"  {incident.summary}",
                        *[f"  evidence: {evidence}" for evidence in incident.evidence],
                        "",
                    ]
                )
        if plans:
            lines.append("REMEDIATION PLANS")
            for plan in plans:
                confirmation = "required" if plan.requires_confirmation else "not required"
                lines.extend(
                    [
                        f"- {plan.action}",
                        f"  risk={plan.risk} • confirmation={confirmation}",
                        f"  reason={plan.reason}",
                        f"  command={plan.command or 'manual review'}",
                    ]
                )
        lines.extend(
            [
                "",
                "Safety boundary: this page is read-only. It diagnoses and plans; it never executes remediation.",
            ]
        )
        self.output.setPlainText("\n".join(lines))
