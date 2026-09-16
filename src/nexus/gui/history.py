from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nexus.observability.history import Observation, read_observations


class HistoryChart(QWidget):
    """Dependency-free line chart for persisted CPU, memory, and disk history."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(300)
        self._observations: list[Observation] = []

    def set_observations(self, observations: list[Observation]) -> None:
        self._observations = observations
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(48, 20, -20, -34)
        painter.setPen(QPen(Qt.GlobalColor.darkGray, 1))
        painter.drawRect(rect)
        if not self._observations:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No persisted observations yet")
            return

        series = {
            "CPU": [item.snapshot["cpu"]["load_percent"] for item in self._observations],
            "Memory": [item.snapshot["memory"]["used_percent"] for item in self._observations],
            "Disk": [item.snapshot["disk"]["used_percent"] for item in self._observations],
        }
        pen_colors = [Qt.GlobalColor.cyan, Qt.GlobalColor.yellow, Qt.GlobalColor.magenta]
        for index, (name, values) in enumerate(series.items()):
            painter.setPen(QPen(pen_colors[index], 2))
            points: list[QPointF] = []
            maximum = max(100.0, max(values))
            width = max(1, rect.width() - 1)
            for point_index, value in enumerate(values):
                x = rect.left() + (width * point_index / max(1, len(values) - 1))
                y = rect.bottom() - (rect.height() * min(maximum, max(0.0, value)) / maximum)
                points.append(QPointF(x, y))
            for first, second in zip(points, points[1:]):
                painter.drawLine(first, second)
            painter.drawText(rect.left() + index * 95, rect.bottom() + 25, f"— {name}")


class HistoryPage(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("detailPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 24)
        title = QLabel("Historical Telemetry")
        title.setObjectName("pageTitle")
        subtitle = QLabel("CPU, memory, and disk pressure across persisted NEXUS observations")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.chart = HistoryChart()
        layout.addWidget(self.chart, 1)
        self.summary = QLabel("No observations loaded")
        self.summary.setObjectName("subtitle")
        layout.addWidget(self.summary)
        self.refresh()

    def refresh(self) -> None:
        observations = read_observations(limit=120)
        self.chart.set_observations(observations)
        if observations:
            self.summary.setText(
                f"{len(observations)} observations • latest {observations[-1].timestamp} • "
                "scale: 0–100%"
            )
        else:
            self.summary.setText("No observations loaded — run nexus-observe to build history.")
