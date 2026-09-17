from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nexus.capture.manager import CaptureBackend, CaptureManager
from nexus.capture.models import CaptureSession, CaptureState
from nexus.capture.policy import CapturePolicy


class FakeCaptureBackend(CaptureBackend):
    name = "fake"

    def available(self) -> bool:
        return True

    def start(self, session: CaptureSession) -> CaptureSession:
        return CaptureSession(session.session_id, CaptureState.RECORDING, session.started_at, session.storage_path)

    def pause(self, session: CaptureSession) -> CaptureSession:
        return CaptureSession(session.session_id, CaptureState.PAUSED, session.started_at, session.storage_path)

    def resume(self, session: CaptureSession) -> CaptureSession:
        return CaptureSession(session.session_id, CaptureState.RECORDING, session.started_at, session.storage_path)

    def stop(self, session: CaptureSession) -> CaptureSession:
        return CaptureSession(session.session_id, CaptureState.OFF, session.started_at, session.storage_path)


class CaptureManagerTests(unittest.TestCase):
    def test_capture_is_disabled_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = CaptureManager(policy=CapturePolicy(storage_root=Path(tmp)), backend=FakeCaptureBackend())
            with self.assertRaises(PermissionError):
                manager.start()

    def test_lifecycle_is_explicit_and_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = CaptureManager(
                policy=CapturePolicy(enabled=True, storage_root=Path(tmp)),
                backend=FakeCaptureBackend(),
            )
            session = manager.start()
            self.assertEqual(session.state, CaptureState.RECORDING)
            self.assertEqual(manager.pause().state, CaptureState.PAUSED)
            self.assertEqual(manager.resume().state, CaptureState.RECORDING)
            self.assertEqual(manager.stop().state, CaptureState.OFF)
            self.assertEqual(len(manager.list()), 4)

    def test_unavailable_backend_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = CaptureManager(policy=CapturePolicy(enabled=True, storage_root=Path(tmp)))
            with self.assertRaisesRegex(RuntimeError, "no safe screen capture backend"):
                manager.start()


if __name__ == "__main__":
    unittest.main()
