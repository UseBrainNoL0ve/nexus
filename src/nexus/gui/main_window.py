from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nexus.doctor import run_checks
from nexus.packages.pacman import inspect_updates
from nexus.sensors.system import collect_snapshot
from nexus.services.systemd import inspect_services


class MetricCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        self.title = QLabel(title)
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        layout.addWidget(self.title)
        layout.addWidget(self.value)

    def set_value(self, value: str) -> None:
        self.value.setText(value)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NEXUS — Linux System Intelligence")
        self.resize(1040, 680)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        header = QFrame()
        header_layout = QGridLayout(header)
        title = QLabel("NEXUS")
        title.setObjectName("appTitle")
        subtitle = QLabel("Linux System Intelligence")
        self.health = QLabel("● Checking")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(title, 0, 0)
        header_layout.addWidget(subtitle, 1, 0)
        header_layout.addWidget(self.health, 0, 1)
        header_layout.addWidget(self.refresh_button, 0, 2)
        layout.addWidget(header)

        metrics = QGridLayout()
        self.cpu = MetricCard("CPU")
        self.memory = MetricCard("Memory")
        self.disk = MetricCard("Disk")
        self.network = MetricCard("Network")
        for index, card in enumerate((self.cpu, self.memory, self.disk, self.network)):
            metrics.addWidget(card, 0, index)
        layout.addLayout(metrics)

        health_frame = QFrame()
        health_layout = QVBoxLayout(health_frame)
        health_layout.addWidget(QLabel("System Health"))
        self.health_details = QLabel("Loading health checks…")
        self.health_details.setWordWrap(True)
        health_layout.addWidget(self.health_details)
        layout.addWidget(health_frame)

        system_frame = QFrame()
        system_layout = QGridLayout(system_frame)
        self.services = MetricCard("Services")
        self.packages = MetricCard("Package Updates")
        system_layout.addWidget(self.services, 0, 0)
        system_layout.addWidget(self.packages, 0, 1)
        layout.addWidget(system_frame)

        self.status = QLabel("Read-only dashboard")
        layout.addWidget(self.status)

        self.setStyleSheet(
            """
            QWidget { background: #111318; color: #e7eaf0; font-size: 14px; }
            QFrame#metricCard, QFrame { background: #181b22; border: 1px solid #292e38; border-radius: 10px; }
            QFrame#metricCard { padding: 8px; }
            QLabel#appTitle { font-size: 28px; font-weight: 700; }
            QLabel#metricValue { font-size: 25px; font-weight: 600; }
            QPushButton { padding: 8px 16px; border-radius: 7px; background: #252a34; }
            QPushButton:hover { background: #303744; }
            QProgressBar { border: 1px solid #292e38; border-radius: 5px; }
            """
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)
        self.refresh()

    def refresh(self) -> None:
        try:
            snapshot = collect_snapshot()
            self.cpu.set_value(f"{snapshot.cpu.load_percent:.1f}%")
            self.memory.set_value(f"{snapshot.memory.used_percent:.1f}%")
            self.disk.set_value(f"{snapshot.disk.used_percent:.1f}%")
            self.network.set_value(str(len(snapshot.network)))

            checks = run_checks(snapshot)
            warnings = [check for check in checks if check.status == "warn"]
            self.health.setText("● Warning" if warnings else "● Healthy")
            self.health_details.setText(
                "\n".join(
                    f"{'⚠' if check.status == 'warn' else '✓'} {check.name}: {check.detail}"
                    for check in checks
                )
            )

            services = inspect_services()
            failed = sum(service.active_state == "failed" for service in services)
            self.services.set_value(f"{len(services)} total / {failed} failed")

            updates = inspect_updates()
            self.packages.set_value(str(len(updates)))
            self.status.setText("Read-only dashboard • refreshed from local system")
        except Exception as exc:
            self.health.setText("● Error")
            self.health_details.setText(str(exc))
            self.status.setText("Dashboard refresh failed")
