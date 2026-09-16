from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from nexus.gui.pages import (
    DetailPage,
    PackagesPage,
    ServicesPage,
    doctor_text,
    history_text,
    scheduler_text,
)
from nexus.gui.workers import DashboardWorker


class MetricCard(QFrame):
    def __init__(self, title: str, icon: str = "") -> None:
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(7)
        heading = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setObjectName("cardIcon")
        title_label = QLabel(title.upper())
        title_label.setObjectName("cardTitle")
        heading.addWidget(icon_label)
        heading.addWidget(title_label)
        heading.addStretch()
        layout.addLayout(heading)
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(5)
        self.bar.hide()
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
        self.resize(1240, 800)
        self.setMinimumSize(1000, 680)
        self.seconds_until_refresh = 2
        self.pulse = False
        self.refreshing = False
        self.refresh_count = 0
        self.worker: DashboardWorker | None = None

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(224)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 20)
        side.setSpacing(7)
        brand = QHBoxLayout()
        logo = QLabel("N")
        logo.setObjectName("logoMark")
        brand_text = QVBoxLayout()
        logo_name = QLabel("NEXUS")
        logo_name.setObjectName("logo")
        logo_subtitle = QLabel("SYSTEM INTELLIGENCE")
        logo_subtitle.setObjectName("logoSubtitle")
        brand_text.addWidget(logo_name)
        brand_text.addWidget(logo_subtitle)
        brand.addWidget(logo)
        brand.addLayout(brand_text)
        side.addLayout(brand)
        side.addSpacing(28)

        nav_items = (("▦", "Dashboard"), ("◈", "Services"), ("□", "Packages"), ("✓", "Doctor"), ("◷", "Scheduler"), ("≡", "History"))
        self.nav_buttons: dict[str, QPushButton] = {}
        for index, (icon, name) in enumerate(nav_items):
            button = QPushButton(f"  {icon}   {name}")
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, page=index: self.show_page(page))
            self.nav_buttons[name] = button
            side.addWidget(button)
        side.addStretch()
        mode = QLabel("●  LOCAL / CONFIRMATION-GATED")
        mode.setObjectName("modeBadge")
        side.addWidget(mode)
        version = QLabel("NEXUS 0.2.0-alpha")
        version.setObjectName("sidebarVersion")
        side.addWidget(version)
        root_layout.addWidget(sidebar)

        self.pages = QStackedWidget()
        root_layout.addWidget(self.pages)
        self._build_dashboard()
        self.pages.addWidget(ServicesPage())
        self.pages.addWidget(PackagesPage())
        self.pages.addWidget(DetailPage("System Doctor", "Deterministic health checks", doctor_text))
        self.pages.addWidget(DetailPage("Scheduler", "Configured recurring NEXUS jobs", scheduler_text))
        self.pages.addWidget(DetailPage("History", "Recent scheduler execution audit", history_text))

        self.setStyleSheet(
            """
            QWidget#root { background: #090c11; color: #e7ebf2; }
            QFrame#sidebar { background: #0c1017; border-right: 1px solid #1c2430; }
            QLabel#logoMark { background: #e7ebf2; color: #0b0f15; border-radius: 10px; min-width: 38px; max-width: 38px; min-height: 38px; max-height: 38px; font-size: 21px; font-weight: 900; qproperty-alignment: AlignCenter; }
            QLabel#logo { font-size: 22px; font-weight: 850; letter-spacing: 2px; }
            QLabel#logoSubtitle { color: #657184; font-size: 8px; font-weight: 700; letter-spacing: 1px; }
            QLabel#pageTitle { font-size: 31px; font-weight: 800; }
            QLabel#subtitle { color: #768297; font-size: 13px; }
            QLabel#cardTitle { color: #778398; font-size: 10px; font-weight: 800; letter-spacing: 1.1px; }
            QLabel#cardIcon { color: #718cff; font-size: 13px; font-weight: 800; }
            QFrame#metricCard, QFrame#panel, QFrame#detailPage { background: #101620; border: 1px solid #202a37; border-radius: 14px; }
            QFrame#metricCard:hover, QFrame#panel:hover { border: 1px solid #2b3849; }
            QLabel#metricValue { font-size: 25px; font-weight: 750; }
            QLabel#healthBadge { background: #13241c; color: #70d59a; border: 1px solid #28533d; border-radius: 15px; padding: 7px 12px; font-weight: 750; }
            QLabel#healthBadgeWarning { background: #2a2115; color: #eeb96e; border: 1px solid #65471f; border-radius: 15px; padding: 7px 12px; font-weight: 750; }
            QLabel#healthDetails { color: #b8c1ce; }
            QLabel#liveText { color: #70d59a; font-weight: 750; }
            QLabel#modeBadge { color: #70d59a; background: #102019; border: 1px solid #234a37; border-radius: 8px; padding: 7px 9px; font-size: 9px; font-weight: 750; }
            QLabel#sidebarVersion { color: #4f5b6d; font-size: 10px; padding-left: 4px; }
            QPushButton#navButton { text-align: left; padding: 11px 10px; border-radius: 9px; background: transparent; color: #7f8a9c; border: 1px solid transparent; font-size: 12px; font-weight: 650; }
            QPushButton#navButton:checked { background: #171e29; color: #f1f4f8; border: 1px solid #252f3d; }
            QPushButton#navButton:hover { background: #141a23; color: #edf1f7; }
            QPushButton#primaryButton, QPushButton#secondaryButton { padding: 9px 15px; border-radius: 9px; font-weight: 750; }
            QPushButton#primaryButton { background: #e7ebf2; color: #10141a; border: 0; }
            QPushButton#primaryButton:hover { background: #ffffff; }
            QPushButton#primaryButton:disabled { background: #343b46; color: #858e9c; }
            QPushButton#secondaryButton { background: #171e29; color: #dbe1ea; border: 1px solid #2a3544; }
            QPushButton#secondaryButton:hover { background: #202a38; border-color: #3a485b; }
            QProgressBar { border: 0; background: #202733; border-radius: 3px; }
            QProgressBar::chunk { background: #718cff; border-radius: 3px; }
            QLabel#statusBar { color: #566174; font-size: 10px; }
            QPlainTextEdit#detailOutput { background: #0b1017; color: #c8d0dc; border: 0; border-radius: 10px; font-family: monospace; font-size: 12px; padding: 12px; }
            QTableWidget { background: #0b1017; color: #c8d0dc; border: 1px solid #202a37; border-radius: 10px; gridline-color: #1b2430; selection-background-color: #202b3b; selection-color: #ffffff; }
            QHeaderView::section { background: #141a23; color: #7f8a9c; border: 0; padding: 9px; font-size: 10px; font-weight: 800; }
            """
        )
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._timer_tick)
        self.timer.start(1000)
        self.show_page(0)
        self.refresh()

    def _build_dashboard(self) -> None:
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 26, 30, 24)
        content_layout.setSpacing(17)
        self.pages.addWidget(content)

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
        self.refresh_button = QPushButton("↻  Refresh Now")
        self.refresh_button.setObjectName("primaryButton")
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(self.refresh_button)
        content_layout.addLayout(header)

        metrics = QGridLayout()
        metrics.setSpacing(13)
        self.cpu = MetricCard("CPU Load", "◉")
        self.memory = MetricCard("Memory", "◒")
        self.disk = MetricCard("Root Disk", "◫")
        self.network = MetricCard("Network", "⌁")
        for index, card in enumerate((self.cpu, self.memory, self.disk, self.network)):
            metrics.addWidget(card, 0, index)
        content_layout.addLayout(metrics)

        middle = QHBoxLayout()
        middle.setSpacing(13)
        health_frame = QFrame()
        health_frame.setObjectName("panel")
        health_layout = QVBoxLayout(health_frame)
        health_layout.setContentsMargins(18, 16, 18, 16)
        health_header = QHBoxLayout()
        health_title = QLabel("System Health")
        health_title.setStyleSheet("font-size: 15px; font-weight: 750;")
        health_header.addWidget(health_title)
        health_header.addStretch()
        self.check_count = QLabel("0 checks")
        self.check_count.setObjectName("subtitle")
        health_header.addWidget(self.check_count)
        health_layout.addLayout(health_header)
        self.health_details = QLabel("Starting live monitor…")
        self.health_details.setObjectName("healthDetails")
        self.health_details.setWordWrap(True)
        health_layout.addWidget(self.health_details)
        middle.addWidget(health_frame, 2)

        activity = QFrame()
        activity.setObjectName("panel")
        activity_layout = QVBoxLayout(activity)
        activity_layout.setContentsMargins(18, 16, 18, 16)
        activity_title = QLabel("Live Monitor")
        activity_title.setStyleSheet("font-size: 15px; font-weight: 750;")
        activity_layout.addWidget(activity_title)
        self.refresh_info = QLabel("●  LIVE")
        self.refresh_info.setObjectName("liveText")
        activity_layout.addWidget(self.refresh_info)
        self.last_updated = QLabel("Last update: —")
        self.last_updated.setObjectName("subtitle")
        activity_layout.addWidget(self.last_updated)
        self.refresh_count_label = QLabel("Refresh cycles: 0")
        self.refresh_count_label.setObjectName("subtitle")
        activity_layout.addWidget(self.refresh_count_label)
        self.system_identity = QLabel("Host: —\nKernel: —")
        self.system_identity.setObjectName("healthDetails")
        activity_layout.addSpacing(8)
        activity_layout.addWidget(self.system_identity)
        activity_layout.addStretch()
        middle.addWidget(activity, 1)
        content_layout.addLayout(middle)

        system_grid = QGridLayout()
        system_grid.setSpacing(13)
        self.services = MetricCard("Systemd Services", "◈")
        self.packages = MetricCard("Package Updates", "□")
        system_grid.addWidget(self.services, 0, 0)
        system_grid.addWidget(self.packages, 0, 1)
        content_layout.addLayout(system_grid)
        self.status = QLabel("LIVE • local system data")
        self.status.setObjectName("statusBar")
        content_layout.addWidget(self.status)

    def show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons.values()):
            button.setChecked(button_index == index)
        page = self.pages.widget(index)
        if isinstance(page, (DetailPage, ServicesPage, PackagesPage)):
            page.refresh()

    def _timer_tick(self) -> None:
        self.seconds_until_refresh -= 1
        self.pulse = not self.pulse
        dot = "●" if self.pulse else "○"
        if self.refreshing:
            self.refresh_info.setText(f"{dot}  LIVE  •  collecting telemetry…")
        elif self.seconds_until_refresh <= 0:
            self.refresh()
        else:
            self.refresh_info.setText(f"{dot}  LIVE  •  next scan in {self.seconds_until_refresh}s")

    def refresh(self) -> None:
        if self.refreshing:
            return
        self.seconds_until_refresh = 2
        self.refreshing = True
        self.refresh_button.setEnabled(False)
        self.health.setText("●  Scanning")
        self.refresh_info.setText("●  LIVE  •  collecting telemetry…")
        worker = DashboardWorker(self)
        worker.data_ready.connect(self._dashboard_ready)
        worker.failed.connect(self._dashboard_failed)
        worker.finished.connect(self._worker_finished)
        self.worker = worker
        worker.start()

    def _dashboard_ready(self, data: object) -> None:
        snapshot = data.snapshot
        checks = data.checks
        services = data.services
        updates = data.updates
        self.cpu.set_value(f"{snapshot.cpu.load_percent:.1f}%", snapshot.cpu.load_percent)
        self.memory.set_value(f"{snapshot.memory.used_percent:.1f}%", snapshot.memory.used_percent)
        self.disk.set_value(f"{snapshot.disk.used_percent:.1f}%", snapshot.disk.used_percent)
        self.network.set_value(f"{len(snapshot.network)} interfaces")
        self.system_identity.setText(f"Host: {snapshot.hostname}\nKernel: {snapshot.kernel}\nPython: {snapshot.python_version}")
        warnings = [check for check in checks if check.status == "warn"]
        self.health.setText("●  Warning" if warnings else "●  Healthy")
        self.health.setObjectName("healthBadgeWarning" if warnings else "healthBadge")
        self.health.style().unpolish(self.health)
        self.health.style().polish(self.health)
        self.check_count.setText(f"{len(checks)} checks")
        self.health_details.setText("\n".join(f"{'⚠' if check.status == 'warn' else '✓'}  {check.name}: {check.detail}" for check in checks))
        failed = sum(service.active_state == "failed" for service in services)
        self.services.set_value(f"{len(services)} total  •  {failed} failed")
        self.packages.set_value(f"{len(updates)} available")
        self.refresh_count += 1
        self.refresh_count_label.setText(f"Refresh cycles: {self.refresh_count}")
        self.last_updated.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        self.status.setText("LIVE • local system data • background scan every 2 seconds")

    def _dashboard_failed(self, message: str) -> None:
        self.health.setText("●  Error")
        self.health_details.setText(message)
        self.status.setText("Dashboard scan failed • will retry automatically")

    def _worker_finished(self) -> None:
        self.refreshing = False
        self.refresh_button.setEnabled(True)
        worker = self.worker
        self.worker = None
        if worker is not None:
            worker.deleteLater()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait()
        event.accept()
