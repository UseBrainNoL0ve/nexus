import subprocess
import unittest

from nexus.packages.pacman import inspect_updates


class PacmanTests(unittest.TestCase):
    def test_update_output_is_parsed(self):
        def fake_runner(command):
            self.assertEqual(command, ("pacman", "-Qu"))
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "core/linux 6.17-1 -> 6.17-2\n"
                    "extra/example 1.2.0-1 -> 1.3.0-1\n"
                ),
                stderr="",
            )

        updates = inspect_updates(fake_runner)
        self.assertEqual(len(updates), 2)
        self.assertEqual(updates[0].repository, "core")
        self.assertEqual(updates[0].name, "linux")
        self.assertEqual(updates[0].current_version, "6.17-1")
        self.assertEqual(updates[0].available_version, "6.17-2")

    def test_no_updates_returns_empty_list(self):
        def fake_runner(command):
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        self.assertEqual(inspect_updates(fake_runner), [])

    def test_pacman_failure_raises(self):
        def fake_runner(command):
            return subprocess.CompletedProcess(command, 2, stdout="", stderr="database error")

        with self.assertRaises(Exception):
            inspect_updates(fake_runner)


if __name__ == "__main__":
    unittest.main()
