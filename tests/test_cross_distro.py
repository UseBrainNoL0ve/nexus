from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from nexus.packages.generic import inspect_updates
from nexus.platform import PackageBackend


class CrossDistroPackageTests(unittest.TestCase):
    def test_apt_update_output(self) -> None:
        backend = PackageBackend("apt", "apt", ("apt", "list", "--upgradable"), ("apt", "upgrade"))
        result = subprocess.CompletedProcess([], 0, "Listing...\nopenssl/stable 3.5.2 amd64 [upgradable from: 3.5.1]\n", "")
        with patch("nexus.packages.generic._runner", return_value=result):
            updates = inspect_updates(backend)
        self.assertEqual([(item.name, item.current_version, item.available_version) for item in updates], [("openssl", "3.5.1", "3.5.2")])

    def test_unknown_backend_has_no_guessing(self) -> None:
        backend = PackageBackend("unknown", "unknown", ("unknown", "inspect"), ("unknown", "update"))
        result = subprocess.CompletedProcess([], 127, "", "not found")
        with patch("nexus.packages.generic._runner", return_value=result):
            self.assertEqual(inspect_updates(backend), [])


if __name__ == "__main__":
    unittest.main()
