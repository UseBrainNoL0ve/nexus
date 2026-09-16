import json
import tempfile
import unittest
from pathlib import Path

from nexus.core.models import CpuSnapshot, DiskSnapshot, MemorySnapshot, NetworkInterface, SystemSnapshot
from nexus.observability.history import analyze_observations, append_observation, read_observations


def snapshot(cpu: float, memory: float, disk: float, rx: int = 100, tx: int = 200) -> SystemSnapshot:
    return SystemSnapshot(
        hostname="test-host",
        platform="Linux",
        kernel="test-kernel",
        python_version="3.14",
        cpu=CpuSnapshot(cpu, 8),
        memory=MemorySnapshot(1000, 500, memory),
        disk=DiskSnapshot("/", 1000, 500, disk),
        network=(NetworkInterface("eth0", rx, tx),),
    )


class ObservabilityTests(unittest.TestCase):
    def test_append_and_read_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            append_observation(snapshot(10, 20, 30), path)
            entries = read_observations(path)

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].snapshot["cpu"]["load_percent"], 10)
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

    def test_analysis_calculates_deltas_and_network_traffic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            append_observation(snapshot(10, 20, 30, 100, 200), path)
            append_observation(snapshot(15, 25, 31, 500, 900), path)
            analysis = analyze_observations(read_observations(path))

            self.assertTrue(analysis["baseline_available"])
            self.assertEqual(analysis["delta"]["cpu_load_percent"], 5)
            self.assertEqual(analysis["delta"]["memory_used_percent"], 5)
            self.assertEqual(analysis["delta"]["disk_used_percent"], 1)
            self.assertEqual(analysis["network_delta"]["eth0"]["rx_bytes_delta"], 400)
            self.assertEqual(analysis["network_delta"]["eth0"]["tx_bytes_delta"], 700)

    def test_empty_analysis_is_explicit(self) -> None:
        self.assertEqual(analyze_observations([]), {"observations": 0, "baseline_available": False})


if __name__ == "__main__":
    unittest.main()
