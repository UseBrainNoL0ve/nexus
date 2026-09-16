import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.scheduler.install import install_user_service, unit_text


class SchedulerInstallTests(unittest.TestCase):
    def test_unit_points_at_current_python_and_daemon(self):
        text = unit_text("/tmp/nexus-python")
        self.assertIn("ExecStart=/tmp/nexus-python -m nexus.scheduler.commands run --daemon", text)
        self.assertIn("Restart=on-failure", text)
        self.assertIn("WantedBy=default.target", text)

    def test_install_writes_unit_without_enabling_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nexus-scheduler.service"
            written = install_user_service(path, "/tmp/nexus-python")
            self.assertEqual(written, path)
            self.assertIn("ExecStart=/tmp/nexus-python", path.read_text(encoding="utf-8"))

    @patch("nexus.scheduler.install.subprocess.run")
    def test_install_module_has_no_implicit_systemctl_side_effect(self, run):
        with tempfile.TemporaryDirectory() as directory:
            install_user_service(Path(directory) / "service", "/tmp/nexus-python")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
