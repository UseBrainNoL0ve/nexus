import unittest

from nexus.core.models import CpuSnapshot, DiskSnapshot, MemorySnapshot, NetworkInterface, SystemSnapshot
from nexus.diagnostics.engine import diagnose_system
from nexus.services.systemd import ServiceSnapshot


class DiagnosticEngineTests(unittest.TestCase):
    def make_snapshot(self, memory=42.0, disk=55.0, network=True):
        return SystemSnapshot(
            hostname="test-host",
            platform="Linux",
            kernel="test-kernel",
            python_version="3.13.0",
            cpu=CpuSnapshot(load_percent=10.0, logical_cores=8),
            memory=MemorySnapshot(total_bytes=100, available_bytes=58, used_percent=memory),
            disk=DiskSnapshot(path="/", total_bytes=100, free_bytes=45, used_percent=disk),
            network=[NetworkInterface(name="eth0", rx_bytes=10, tx_bytes=20)] if network else [],
        )

    def test_healthy_snapshot_has_no_findings_without_optional_evidence(self):
        findings = diagnose_system(self.make_snapshot())
        self.assertEqual(findings, [])

    def test_resource_findings_are_structured(self):
        findings = diagnose_system(self.make_snapshot(memory=92.0, disk=88.0))
        self.assertEqual([finding.id for finding in findings], ["disk-pressure", "memory-pressure"])
        self.assertTrue(all(finding.severity == "warning" for finding in findings))

    def test_failed_service_is_reported(self):
        service = ServiceSnapshot(
            unit="example.service",
            load_state="loaded",
            active_state="failed",
            sub_state="failed",
            description="Example service",
            enabled_state="enabled",
        )
        findings = diagnose_system(self.make_snapshot(), services=[service])
        self.assertEqual(findings[0].id, "failed-service:example.service")
        self.assertIn("example.service", findings[0].evidence)

    def test_package_updates_are_informational_but_confirmation_gated(self):
        findings = diagnose_system(self.make_snapshot(), update_count=12)
        self.assertEqual(findings[0].id, "package-updates-available")
        self.assertEqual(findings[0].severity, "info")
        self.assertTrue(findings[0].requires_confirmation)


if __name__ == "__main__":
    unittest.main()
