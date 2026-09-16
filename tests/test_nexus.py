import unittest

from nexus.core.models import CpuSnapshot, DiskSnapshot, MemorySnapshot, NetworkInterface, SystemSnapshot
from nexus.doctor import run_checks
from nexus.reporting import snapshot_to_json


class NEXUSTests(unittest.TestCase):
    def snapshot(self, memory=40.0, disk=50.0):
        return SystemSnapshot(
            hostname="test-host",
            platform="Linux",
            kernel="test-kernel",
            python_version="3.13.0",
            cpu=CpuSnapshot(10.0, 8),
            memory=MemorySnapshot(100, 60, memory),
            disk=DiskSnapshot("/", 100, 50, disk),
            network=(NetworkInterface("lo", 100, 100),),
        )

    def test_healthy_snapshot_has_no_warnings(self):
        results = run_checks(self.snapshot())
        self.assertTrue(all(item.status == "ok" for item in results))

    def test_high_disk_usage_warns(self):
        results = run_checks(self.snapshot(disk=90.0))
        disk = next(item for item in results if item.name == "disk")
        self.assertEqual(disk.status, "warn")

    def test_report_is_json(self):
        payload = snapshot_to_json(self.snapshot())
        self.assertIn('"hostname": "test-host"', payload)


if __name__ == "__main__":
    unittest.main()
