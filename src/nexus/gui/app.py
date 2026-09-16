from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QPushButton

from nexus.gui.history import HistoryPage
from nexus.gui.incidents import IncidentCenterPage
from nexus.gui.main_window import MainWindow
from nexus.gui.operations import OperationsPage


class NexusDesktopWindow(MainWindow):
    """Main NEXUS window with investigation and operations surfaces."""

    def __init__(self) -> None:
        super().__init__()
        operations = OperationsPage()
        operations_index = self.pages.addWidget(operations)
        incident_index = self.pages.addWidget(IncidentCenterPage())
        history_index = self.pages.addWidget(HistoryPage())

        entries = (
            ("Command Center", "  ⚙   Command Center", operations_index),
            ("Incidents", "  ◉   Incidents", incident_index),
            ("Telemetry", "  ◒   Telemetry", history_index),
        )
        sidebar = self.nav_buttons["History"].parentWidget()
        if sidebar is None or sidebar.layout() is None:
            return
        for offset, (name, label, index) in enumerate(entries):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, page=index: self.show_page(page))
            self.nav_buttons[name] = button
            sidebar.layout().insertWidget(8 + offset, button)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NEXUS")
    window = NexusDesktopWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
