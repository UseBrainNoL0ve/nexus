import subprocess
import unittest

from nexus.packages.actions import plan_package_updates
from nexus.packages.engine import execute_package_update
from nexus.packages.pacman import PackageUpdate


class PackageEngineTests(unittest.TestCase):
    def proposal(self):
        return plan_package_updates([
            PackageUpdate("linux", "core", "6.17-1", "6.17-2"),
        ])[0]

    def test_unconfirmed_update_does_not_execute(self):
        calls = []

        def fake_runner(command):
            calls.append(tuple(command))
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        result = execute_package_update(self.proposal(), confirmed=False, runner=fake_runner)
        self.assertFalse(result.executed)
        self.assertIsNone(result.return_code)
        self.assertEqual(calls, [])
        self.assertIn("Confirmation required", result.stderr)

    def test_confirmed_update_uses_injected_runner(self):
        calls = []

        def fake_runner(command):
            calls.append(tuple(command))
            return subprocess.CompletedProcess(command, 0, stdout="updated\n", stderr="")

        result = execute_package_update(self.proposal(), confirmed=True, runner=fake_runner)
        self.assertTrue(result.executed)
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout, "updated\n")
        self.assertEqual(calls, [("sudo", "pacman", "-S", "core/linux")])

    def test_runner_failure_is_returned(self):
        def fake_runner(command):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="transaction failed\n")

        result = execute_package_update(self.proposal(), confirmed=True, runner=fake_runner)
        self.assertTrue(result.executed)
        self.assertEqual(result.return_code, 1)
        self.assertEqual(result.stderr, "transaction failed\n")

    def test_proposal_must_require_confirmation(self):
        proposal = self.proposal()
        proposal = type(proposal)(
            package=proposal.package,
            repository=proposal.repository,
            current_version=proposal.current_version,
            available_version=proposal.available_version,
            risk=proposal.risk,
            requires_confirmation=False,
        )

        with self.assertRaises(ValueError):
            execute_package_update(proposal, confirmed=True)


if __name__ == "__main__":
    unittest.main()
