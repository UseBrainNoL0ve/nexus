from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
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
    def __init__(self, title: str, suffix: str = "") -> None:
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        self.title = QLabel(title.upper())
        self.title.setObjectName("cardTitle")
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        self.suffix = suffix
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(5)
        self.bar.hide()
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.bar)

    def set_value(self, value: str, progress: float | None = None) -> None:
        self.value.setText(value)
        if progress is None:
            self.bar.hide()
        else:
            self.bar.show()
            self.bar.setValue(max(0, min(100, int(progress))))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NEXUS — Linux System Intelligence")
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)
        self.refresh_interval_ms = 5000
        self.seconds_until_refresh = 5

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 28, 20, 20)
        side.setSpacing(8)

        logo = QLabel("NEXUS")
        logo.setObjectName("logo")
        side.addWidget(logo)
        side.addWidget(QLabel("SYSTEM INTELLIGENCE"))
        side.addSpacing(24)
        for name in ("Dashboard", "Services", "Packages", "Doctor", "History"):
            button = QPushButton(name)
            button.setObjectName("navButton")
            button.setEnabled(name == "Dashboard")
            side.addWidget(button)
        side.addStretch()
        readonly = QLabel("READ-ONLY MODE")
        readonly.setObjectName("readonlyBadge")
        side.addWidget(readonly)
        root_layout.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 26, 30, 24)
        content_layout.setSpacing(18)
        root_layout.addWidget(content)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("System Overview")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Live telemetry from your CachyOS machine")
        subtitle.setObjectName("subtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()

        self.health = QLabel("●  Checking")
        self.health.setObjectName("healthBadge")
        header.addWidget(self.health)
        self.refresh_button = QPushButton("Refresh now")
        self.refresh_button.setObjectName("primaryButton")
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(self.refresh_button)
        content_layout.addLayout(header)

        metrics = QGridLayout()
        metrics.setSpacing(14)
        self.cpu = MetricCard("CPU", "%")
        self.memory = MetricCard("Memory", "%")
        self.disk = MetricCard("Disk", "%")
        self.network = MetricCard("Network")
        for index, card in enumerate((self.cpu, self.memory, self.disk, self.network)):
            metrics.addWidget(card, 0, index)
        content_layout.addLayout(metrics)

        middle = QHBoxLayout()
        middle.setSpacing(14)

        health_frame = QFrame()
        health_frame.setObjectName("panel")
        health_layout = QVBoxLayout(health_frame)
        health_header = QHBoxLayout()
        health_header.addWidget(QLabel("System Health"))
        health_header.addStretch()
        health_header.addWidget(QLabel("5 checks"))
        health_layout.addLayout(health_header)
        self.health_details = QLabel("Loading health checks…")
        self.health_details.setObjectName("healthDetails")
        self.health_details.setWordWrap(True)
        health_layout.addWidget(self.health_details)
        middle.addWidget(health_frame, 2)

        activity = QFrame()
        activity.setObjectName("panel")
        activity_layout = QVBoxLayout(activity)
        activity_layout.addWidget(QLabel("Live Monitor"))
        self.refresh_info = QLabel("Auto-refresh: ON")
        self.refresh_info.setObjectName("liveText")
        activity_layout.addWidget(self.refresh_info)
        self.last_updated = QLabel("Last update: —")
        activity_layout.addWidget(self.last_updated)
        activity_layout.addStretch()
        middle.addWidget(activity, 1)
        content_layout.addLayout(middle)

        system_grid = QGridLayout()
        system_grid.setSpacing(14)
        self.services = MetricCard("Systemd Services")
        self.packages = MetricCard("Package Updates")
        system_grid.addWidget(self.services, 0, 0)
        system_grid.addWidget(self.packages, 0, 1)
        content_layout.addLayout(system_grid)

        self.status = QLabel("Read-only dashboard")
        self.status.setObjectName("statusBar")
        content_layout.addWidget(self.status)

        self.setStyleSheet(
            """
            QWidget#root { background: #0b0e13; color: #e7ebf2; }
            QFrame#sidebar { background: #0f131a; border-right: 1px solid #202631; }
            QLabel#logo { font-size: 27px; font-weight: 800; letter-spacing: 2px; }
            QLabel#pageTitle { font-size: 30px; font-weight: 750; }
            QLabel#subtitle { color: #7f8a9a; font-size: 13px; }
            QLabel#cardTitle { color: #7f8a9a; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QFrame#metricCard, QFrame#panel { background: #121720; border: 1px solid #222a36; border-radius: 12px; }
            QFrame#metricCard { padding: 5px; }
            QLabel#metricValue { font-size: 27px; font-weight: 700; }
            QLabel#healthBadge { background: #17261f; color: #71d39b; border: 1px solid #28553e; border-radius: 16px; padding: 7px 12px; font-weight: 700; }
            QLabel#healthBadgeWarning { background: #302718; color: #f0bd70; border: 1px solid #6b4b22; border-radius: 16px; padding: 7px 12px; font-weight: 700; }
            QLabel#healthDetails { color: #b8c1ce; line-height: 1.5; }
            QLabel#liveText { color: #71d39b; font-weight: 700; }
            QLabel#readonlyBadge { color: #7f8a9a; border: 1px solid #29313d; border-radius: 8px; padding: 6px; }
            QPushButton#navButton { text-align: left; padding: 10px 12px; border-radius: 7px; background: transparent; color: #9ba6b5; }
            QPushButton#navButton:enabled { background: #1b222d; color: #edf1f7; }
            QPushButton#navButton:hover { background: #1b222d; color: #edf1f7; }
            QPushButton#primaryButton { background: #e7ebf2; color: #10141a; padding: 9px 15px; border-radius: 8px; font-weight: 700; }
            QPushButton#primaryButton:hover { background: #ffffff; }
            QProgressBar { border: 0; background: #202733; border-radius: 3px; }
            QProgressBar::chunk { background: #6f8cff; border-radius: 3px; }
            QLabel#statusBar { color: #697586; font-size: 11px; }
            """
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._timer_tick)
        self.timer.start(1000)
        self.refresh()

    def _timer_tick(self) -> None:
        self.seconds_until_refresh -= 1
        if self.seconds_until_refresh <= 0:
            self.refresh()
        else:
            self.refresh_info.setText(
                f"Auto-refresh: ON  •  next refresh in {self.seconds_until_refresh}s"
            )

    def refresh(self) -> None:
        self.seconds_until_refresh = 5
        self.refresh_button.setEnabled(False)
        try:
            snapshot = collect_snapshot()
            self.cpu.set_value(f"{snapshot.cpu.load_percent:.1f}%", snapshot.cpu.load_percent)
            self.memory.set_value(f"{snapshot.memory.used_percent:.1f}%", snapshot.memory.used_percent)
            self.disk.set_value(f"{snapshot.disk.used_percent:.1f}%", snapshot.disk.used_percent)
            self.network.set_value(f"{len(snapshot.network)} interfaces")

            checks = run_checks(snapshot)
            warnings = [check for check in checks if check.status == "warn"]
            self.health.setText("●  Warning" if warnings else "●  Healthy")
            self.health.setObjectName("healthBadgeWarning" if warnings else "healthBadge")
            self.health.style().unpolish(self.health)
            self.health.style().polish(self.health)
            self.health_details.setText(
                "\n".join(
                    f"{'⚠' if check.status == 'warn' else '✓'}  {check.name}: {check.detail}"
                    for check in checks
                )
            )

            services = inspect_services()
            failed = sum(service.active_state == "failed" for service in services)
            self.services.set_value(f"{len(services)} total  •  {failed} failed")

            updates = inspect_updates()
            self.packages.set_value(f"{len(updates)} available")
            self.last_updated.setText("Last update: just now")
            self.refresh_info.setText("Auto-refresh: ON  •  next refresh in 5s")
            self.status.setText("READ-ONLY • local system data • automatic refresh every 5 seconds")
        except Exception as exc:
            self.health.setText("●  Error")
            self.health_details.setText(str(exc))
            self.status.setText("Dashboard refresh failed")
        finally:
            self.refresh_button.setEnabled(True)
