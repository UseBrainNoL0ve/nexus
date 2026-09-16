import contextlib
import io
import json
import unittest
from unittest.mock import patch

from nexus.cli import _inspect_packages, _print_diagnose, _print_doctor, _print_services, _print_status, build_parser
from nexus.core.models import CpuSnapshot, DiskSnapshot, MemorySnapshot, NetworkInterface, SystemSnapshot
from nexus.diagnostics.engine import DiagnosticFinding
from nexus.diagnostics.incidents import Incident
from nexus.diagnostics.remediation import RemediationStep
from nexus.packages.pacman import PackageUpdate
from nexus.services.systemd import ServiceSnapshot, SystemdError


class StatusCliTests(unittest.TestCase):
    def _snapshot(self):
        return SystemSnapshot(
            hostname="nexus-host",
            platform="Linux",
            kernel="6.17.1-cachyos",
            python_version="3.13.7",
            cpu=CpuSnapshot(load_percent=12.5, logical_cores=16),
            memory=MemorySnapshot(total_bytes=160000, available_bytes=90000, used_percent=43.75),
            disk=DiskSnapshot(path="/", total_bytes=1000000, free_bytes=400000, used_percent=60.0),
            network=(NetworkInterface(name="enp0s3", rx_bytes=1234, tx_bytes=5678),),
        )

    def test_status_json_output_is_machine_readable(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            _print_status(self._snapshot(), json_output=True)

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["platform"], "Linux")
        self.assertEqual(payload["kernel"], "6.17.1-cachyos")
        self.assertEqual(payload["hostname"], "nexus-host")
        self.assertEqual(payload["cpu"]["logical_cores"], 16)
        self.assertEqual(payload["memory"]["used_percent"], 43.75)
        self.assertEqual(payload["disk"]["path"], "/")
        self.assertEqual(payload["network"][0]["name"], "enp0s3")
        self.assertTrue(payload["read_only"])

    def test_status_parser_accepts_json_flag(self):
        args = build_parser().parse_args(["status", "--json"])
        self.assertEqual(args.command, "status")
        self.assertTrue(args.json)


class DoctorCliTests(unittest.TestCase):
    def _snapshot(self, memory=43.75, disk=60.0, network=True):
        return SystemSnapshot(
            hostname="nexus-host",
            platform="Linux",
            kernel="6.17.1-cachyos",
            python_version="3.13.7",
            cpu=CpuSnapshot(load_percent=12.5, logical_cores=16),
            memory=MemorySnapshot(total_bytes=160000, available_bytes=90000, used_percent=memory),
            disk=DiskSnapshot(path="/", total_bytes=1000000, free_bytes=400000, used_percent=disk),
            network=(NetworkInterface(name="enp0s3", rx_bytes=1234, tx_bytes=5678),) if network else (),
        )

    def test_doctor_json_output_is_machine_readable(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = _print_doctor(self._snapshot(), json_output=True)

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(len(payload["checks"]), 5)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["checks"][0]["name"], "platform")
        self.assertEqual(payload["checks"][2]["status"], "ok")

    def test_doctor_json_output_reports_warning(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = _print_doctor(self._snapshot(memory=95.0), json_output=True)

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload["status"], "warn")
        memory_check = next(check for check in payload["checks"] if check["name"] == "memory")
        self.assertEqual(memory_check["status"], "warn")

    def test_doctor_parser_accepts_json_flag(self):
        args = build_parser().parse_args(["doctor", "--json"])
        self.assertEqual(args.command, "doctor")
        self.assertTrue(args.json)


class DiagnoseCliTests(unittest.TestCase):
    def _finding(self, severity="warning"):
        return DiagnosticFinding(
            id="memory-pressure",
            category="resource",
            severity=severity,
            title="Memory pressure is persistent",
            evidence="Memory usage exceeded 90% in the latest observations.",
            recommendation="Review memory-heavy processes before taking action.",
            requires_confirmation=False,
        )

    def test_diagnose_parser_accepts_json_flag(self):
        args = build_parser().parse_args(["diagnose", "--json"])
        self.assertEqual(args.command, "diagnose")
        self.assertTrue(args.json)

    def test_diagnose_json_is_read_only_and_structured(self):
        finding = self._finding()
        incident = Incident(
            id="incident-resource",
            title="Resource pressure",
            summary="Persistent memory pressure was detected.",
            severity="warning",
            finding_ids=(finding.id,),
            requires_confirmation=False,
        )
        step = RemediationStep(
            action="review-memory-pressure",
            reason="Inspect resource usage before changing the system.",
            risk="low",
            requires_confirmation=False,
            command=None,
        )
        output = io.StringIO()
        with patch(
            "nexus.cli.collect_diagnostics",
            return_value=([finding], []),
        ), patch("nexus.cli.build_incidents", return_value=[incident]), patch(
            "nexus.cli.build_remediation_plan", return_value=[step]
        ), contextlib.redirect_stdout(output):
            code = _print_diagnose(self._snapshot(), json_output=True)

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload["finding_count"], 1)
        self.assertEqual(payload["incident_count"], 1)
        self.assertEqual(payload["findings"][0]["id"], "memory-pressure")
        self.assertEqual(payload["remediation_steps"][0]["action"], "review-memory-pressure")
        self.assertTrue(payload["read_only"])

    def test_diagnose_healthy_system_has_zero_exit_code(self):
        output = io.StringIO()
        with patch("nexus.cli.collect_diagnostics", return_value=([], [])), patch(
            "nexus.cli.build_incidents", return_value=[]
        ), patch("nexus.cli.build_remediation_plan", return_value=[]), contextlib.redirect_stdout(output):
            code = _print_diagnose(self._snapshot(), json_output=False)

        self.assertEqual(code, 0)
        self.assertIn("System signals look normal", output.getvalue())


class PackageCliTests(unittest.TestCase):
    def test_packages_json_output_is_machine_readable(self):
        updates = [
            PackageUpdate(
                name="linux",
                current_version="6.17-1",
                available_version="6.17-2",
                repository="core",
            )
        ]
        output = io.StringIO()
        with patch("nexus.cli.inspect_updates", return_value=updates):
            with contextlib.redirect_stdout(output):
                code, returned = _inspect_packages(json_output=True)

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(returned, updates)
        self.assertEqual(payload["package_manager"], "pacman")
        self.assertEqual(payload["count"], 1)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["updates"][0]["repository"], "core")
        self.assertEqual(payload["updates"][0]["name"], "linux")

    def test_packages_json_output_handles_no_updates(self):
        output = io.StringIO()
        with patch("nexus.cli.inspect_updates", return_value=[]):
            with contextlib.redirect_stdout(output):
                code, returned = _inspect_packages(json_output=True)

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(returned, [])
        self.assertEqual(payload["updates"], [])
        self.assertEqual(payload["count"], 0)
        self.assertTrue(payload["read_only"])

    def test_packages_parser_accepts_json_flag(self):
        args = build_parser().parse_args(["packages", "--json"])
        self.assertEqual(args.command, "packages")
        self.assertTrue(args.json)
        self.assertIsNone(args.package_action)


class ServiceCliTests(unittest.TestCase):
    def _service(self, unit="NetworkManager.service", active="active", enabled="enabled"):
        return ServiceSnapshot(
            unit=unit,
            load_state="loaded",
            active_state=active,
            sub_state="running" if active == "active" else active,
            description="Test service",
            enabled_state=enabled,
        )

    def test_services_json_output_is_machine_readable(self):
        services = [
            self._service(),
            self._service("example.service", active="failed", enabled="disabled"),
        ]
        output = io.StringIO()
        with patch("nexus.cli.inspect_services", return_value=services):
            with contextlib.redirect_stdout(output):
                code = _print_services(json_output=True)

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["service_manager"], "systemd")
        self.assertEqual(payload["count"], 2)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["summary"]["running"], 1)
        self.assertEqual(payload["summary"]["failed"], 1)
        self.assertEqual(payload["summary"]["enabled"], 1)
        self.assertEqual(payload["services"][0]["unit"], "NetworkManager.service")

    def test_services_json_output_handles_inspection_failure(self):
        output = io.StringIO()
        with patch("nexus.cli.inspect_services", side_effect=SystemdError("systemctl unavailable")):
            with contextlib.redirect_stdout(output):
                code = _print_services(json_output=True)

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload["service_manager"], "systemd")
        self.assertEqual(payload["services"], [])
        self.assertEqual(payload["count"], 0)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["error"], "systemctl unavailable")

    def test_services_parser_accepts_json_flag(self):
        args = build_parser().parse_args(["services", "--json"])
        self.assertEqual(args.command, "services")
        self.assertTrue(args.json)


if __name__ == "__main__":
    unittest.main()
