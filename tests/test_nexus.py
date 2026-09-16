import subprocess
import unittest

from nexus.automation.planner import plan_actions
from nexus.automation.rules import evaluate_rules
from nexus.core.models import CpuSnapshot, DiskSnapshot, MemorySnapshot, NetworkInterface, SystemSnapshot
from nexus.doctor import run_checks
from nexus.reporting import snapshot_to_json
from nexus.services.actions import plan_service_action
from nexus.services.systemd import inspect_services


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

    def test_automation_triggers_disk_pressure(self):
        results = evaluate_rules(self.snapshot(disk=90.0))
        disk = next(item for item in results if item.rule == "disk-pressure")
        self.assertTrue(disk.triggered)
        self.assertEqual(disk.action, "propose-cleanup-analysis")

    def test_automation_is_quiet_for_healthy_snapshot(self):
        results = evaluate_rules(self.snapshot())
        self.assertTrue(all(not item.triggered for item in results))

    def test_action_planner_requires_confirmation(self):
        results = evaluate_rules(self.snapshot(disk=90.0))
        proposals = plan_actions(results)
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].action_id, "cleanup-analysis")
        self.assertEqual(proposals[0].risk, "low")
        self.assertTrue(proposals[0].requires_confirmation)

    def test_action_planner_ignores_non_triggered_rules(self):
        results = evaluate_rules(self.snapshot())
        self.assertEqual(plan_actions(results), [])

    def test_systemd_service_inspection_parses_read_only_state(self):
        def fake_runner(command):
            if command[1] == "list-units":
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=(
                        "NetworkManager.service loaded active running "
                        "Network Manager\n"
                        "example.service loaded failed failed Example service\n"
                    ),
                    stderr="",
                )
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "NetworkManager.service enabled enabled\n"
                    "example.service disabled disabled\n"
                ),
                stderr="",
            )

        services = inspect_services(fake_runner)
        self.assertEqual([service.unit for service in services], [
            "NetworkManager.service",
            "example.service",
        ])
        self.assertEqual(services[0].active_state, "active")
        self.assertEqual(services[0].enabled_state, "enabled")
        self.assertEqual(services[1].active_state, "failed")
        self.assertEqual(services[1].enabled_state, "disabled")

    def test_service_action_plan_is_non_executing(self):
        proposal = plan_service_action("NetworkManager.service", "restart")
        self.assertEqual(proposal.command, ("systemctl", "restart", "NetworkManager.service"))
        self.assertEqual(proposal.risk, "medium")
        self.assertTrue(proposal.requires_confirmation)

    def test_service_stop_has_higher_risk(self):
        proposal = plan_service_action("example.service", "stop")
        self.assertEqual(proposal.risk, "high")

    def test_service_action_rejects_invalid_unit(self):
        with self.assertRaises(ValueError):
            plan_service_action("NetworkManager", "restart")

    def test_service_action_rejects_unsupported_action(self):
        with self.assertRaises(ValueError):
            plan_service_action("NetworkManager.service", "reload")


if __name__ == "__main__":
    unittest.main()
