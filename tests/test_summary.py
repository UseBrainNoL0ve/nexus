import unittest
from unittest.mock import patch

from nexus.core.models import CpuSnapshot, DiskSnapshot, MemorySnapshot, NetworkInterface, SystemSnapshot
from nexus.packages.pacman import PackageUpdate
from nexus.scheduler.models import ScheduledJob
from nexus.services.systemd import ServiceSnapshot
from nexus.summary import collect_summary, format_summary


class SummaryTests(unittest.TestCase):
    def snapshot(self):
        return SystemSnapshot(
            hostname="nexus-test",
            platform="Linux",
            kernel="6.17-cachyos",
            python_version="3.14",
            cpu=CpuSnapshot(load_percent=10.0, logical_cores=8),
            memory=MemorySnapshot(total_bytes=1000, available_bytes=400, used_percent=60.0),
            disk=DiskSnapshot(path="/", total_bytes=1000, free_bytes=300, used_percent=70.0),
            network=(NetworkInterface(name="enp1s0", rx_bytes=1, tx_bytes=2),),
        )

    def test_summary_joins_subsystem_state(self):
        service = ServiceSnapshot("example.service", "loaded", "failed", "failed", "Example", "disabled")
        update = PackageUpdate("linux", "6.1-1", "6.1-2", "core")
        job = ScheduledJob("doctor", "doctor", 60)
        with patch("nexus.summary.collect_snapshot", return_value=self.snapshot()), \
             patch("nexus.summary.run_checks", return_value=[]), \
             patch("nexus.summary.overall_status", return_value="healthy"), \
             patch("nexus.summary.inspect_services", return_value=[service]), \
             patch("nexus.summary.inspect_updates", return_value=[update]), \
             patch("nexus.summary.ScheduleStore.load", return_value=[job]):
            payload = collect_summary()

        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["services"]["failed"], 1)
        self.assertEqual(payload["packages"]["updates"], 1)
        self.assertEqual(payload["scheduler"]["jobs"], 1)
        self.assertTrue(payload["read_only"])

    def test_summary_format_mentions_actionable_findings(self):
        payload = {
            "status": "warn",
            "host": "nexus-test",
            "cpu_load_percent": 10.0,
            "memory_used_percent": 60.0,
            "disk_used_percent": 70.0,
            "network_interfaces": 1,
            "services": {"running": 2, "failed": 1, "count": 3, "failed_units": ["example.service"]},
            "packages": {"updates": 1, "items": [{"repository": "core", "name": "linux", "current_version": "6.1-1", "available_version": "6.1-2"}]},
            "scheduler": {"enabled": 1, "due": 1, "jobs": 1},
        }
        output = format_summary(payload)
        self.assertIn("example.service", output)
        self.assertIn("core/linux", output)
        self.assertIn("Health:    WARN", output)


if __name__ == "__main__":
    unittest.main()
