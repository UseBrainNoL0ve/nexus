from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.capture.backends import PortalCapability, WaylandPortalBackend, detect_portal_capability
from nexus.platform import detect_distribution, detect_package_backend


class LinuxCompatibilityTests(unittest.TestCase):
    def test_distribution_parser_covers_common_derivatives(self) -> None:
        samples = {
            "Pardus": 'ID=pardus\nID_LIKE=debian\nNAME="Pardus"\nVERSION_ID="23"\n',
            "Ubuntu": 'ID=ubuntu\nID_LIKE=debian\nNAME="Ubuntu"\nVERSION_ID="24.04"\n',
            "Fedora": 'ID=fedora\nID_LIKE="rhel fedora"\nNAME="Fedora Linux"\nVERSION_ID="42"\n',
            "Kali": 'ID=kali\nID_LIKE=debian\nNAME="Kali GNU/Linux"\nVERSION_ID="2026.2"\n',
            "Parrot": 'ID=parrot\nID_LIKE=debian\nNAME="Parrot OS"\nVERSION_ID="7"\n',
        }
        for name, content in samples.items():
            with self.subTest(distribution=name), tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                detected = detect_distribution(Path(handle.name))
            self.assertNotEqual(detected.id, "unknown")

    def test_package_backend_prefers_distro_family(self) -> None:
        cases = {
            "ubuntu": "apt",
            "pardus": "apt",
            "kali": "apt",
            "parrot": "apt",
            "fedora": "dnf",
            "cachyos": "pacman",
        }
        for distro_id, expected in cases.items():
            with self.subTest(distribution=distro_id):
                with patch("nexus.platform.detect_distribution", return_value=type("D", (), {"id": distro_id})()):
                    with patch("nexus.platform.shutil.which", side_effect=lambda name: name):
                        backend = detect_package_backend()
                self.assertIsNotNone(backend)
                self.assertEqual(backend.name, expected)

    def test_wayland_portal_capability_is_fail_closed(self) -> None:
        capability = detect_portal_capability(
            {"XDG_SESSION_TYPE": "x11"},
            which=lambda _: "/usr/bin/gdbus",
            runner=lambda *args, **kwargs: None,
        )
        self.assertFalse(capability.available)
        self.assertFalse(WaylandPortalBackend(capability).available())

    def test_wayland_portal_capability_requires_successful_ping(self) -> None:
        completed = type("Result", (), {"returncode": 0})()
        capability = detect_portal_capability(
            {"XDG_SESSION_TYPE": "wayland"},
            which=lambda _: "/usr/bin/gdbus",
            runner=lambda *args, **kwargs: completed,
        )
        self.assertEqual(
            capability,
            PortalCapability("wayland", portal_available=True, gdbus_available=True),
        )

    def test_portal_backend_does_not_fake_recording(self) -> None:
        backend = WaylandPortalBackend(PortalCapability("wayland", True, True))
        with self.assertRaises(RuntimeError):
            backend.start(object())


if __name__ == "__main__":
    unittest.main()
