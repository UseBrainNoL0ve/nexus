import contextlib
import io
import json
import unittest
from unittest.mock import patch

from nexus.cli import _inspect_packages, build_parser
from nexus.packages.pacman import PackageUpdate


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


if __name__ == "__main__":
    unittest.main()
