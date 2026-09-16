import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import patch

from nexus.cli import _inspect_packages, _print_services, _print_status, build_parser
from nexus.core.models import CpuSnapshot, DiskSnapshot, MemorySnapshot, NetworkInterface, SystemSnapshot
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
