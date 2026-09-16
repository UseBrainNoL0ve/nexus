from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QPushButton

from nexus.gui.main_window import MainWindow
from nexus.gui.operations import OperationsPage


class NexusDesktopWindow(MainWindow):
    """Main NEXUS window with the CLI operations exposed in the GUI."""

    def __init__(self) -> None:
        super().__init__()
        operations = OperationsPage()
        index = self.pages.addWidget(operations)

        button = QPushButton("  ⚙   Command Center")
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.clicked.connect(lambda checked=False: self.show_page(index))
        self.nav_buttons["Command Center"] = button

        sidebar = self.nav_buttons["History"].parentWidget()
        if sidebar is not None and sidebar.layout() is not None:
            # Insert immediately before the stretch so the command entry stays
            # with the rest of the primary navigation.
            sidebar.layout().insertWidget(8, button)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NEXUS")
    window = NexusDesktopWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
