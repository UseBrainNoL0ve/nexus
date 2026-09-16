import unittest

from nexus.observability.anomalies import detect_trends
from nexus.observability.history import Observation


class HistoricalAnomalyTests(unittest.TestCase):
    def make_observation(self, memory=50.0, disk=50.0, cpu=20.0):
        return Observation(
            timestamp="2026-09-16T12:00:00+00:00",
            snapshot={
                "cpu": {"load_percent": cpu},
                "memory": {"used_percent": memory},
                "disk": {"used_percent": disk},
            },
        )

    def test_insufficient_history_produces_no_findings(self):
        observations = [self.make_observation(memory=95.0) for _ in range(2)]
        self.assertEqual(detect_trends(observations), [])

    def test_persistent_memory_pressure_is_reported(self):
        observations = [self.make_observation(memory=91.0) for _ in range(3)]
        findings = detect_trends(observations)
        self.assertEqual([finding.metric for finding in findings], ["memory_used_percent"])
        self.assertEqual(findings[0].severity, "warning")

    def test_single_spike_is_not_called_an_anomaly(self):
        observations = [
            self.make_observation(memory=50.0),
            self.make_observation(memory=96.0),
            self.make_observation(memory=55.0),
        ]
        self.assertEqual(detect_trends(observations), [])

    def test_multiple_persistent_conditions_are_sorted(self):
        observations = [self.make_observation(memory=92.0, disk=88.0, cpu=85.0) for _ in range(3)]
        findings = detect_trends(observations)
        self.assertEqual(
            [finding.metric for finding in findings],
            ["disk_used_percent", "memory_used_percent", "cpu_load_percent"],
        )


if __name__ == "__main__":
    unittest.main()
