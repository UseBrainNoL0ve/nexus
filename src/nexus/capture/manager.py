from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from nexus.capture.models import CaptureSession, CaptureState
from nexus.capture.policy import CapturePolicy
from nexus.capture.storage import append_session, list_sessions, new_session


class CaptureBackend:
    """Interface implemented by a real screen-capture backend later."""

    name = "unavailable"

    def available(self) -> bool:
        return False

    def start(self, session: CaptureSession) -> CaptureSession:
        raise RuntimeError("no safe screen capture backend is available")

    def pause(self, session: CaptureSession) -> CaptureSession:
        raise RuntimeError("capture backend does not support pause")

    def resume(self, session: CaptureSession) -> CaptureSession:
        raise RuntimeError("capture backend does not support resume")

    def stop(self, session: CaptureSession) -> CaptureSession:
        raise RuntimeError("capture backend does not support stop")


class CaptureManager:
    """Own the capture state machine and policy boundary."""

    def __init__(self, policy: CapturePolicy | None = None, backend: CaptureBackend | None = None) -> None:
        self.policy = policy or CapturePolicy()
        self.backend = backend or CaptureBackend()

    def status(self) -> CaptureSession | None:
        sessions = list_sessions(self.policy.storage_root)
        return sessions[-1] if sessions else None

    def list(self) -> list[CaptureSession]:
        return list_sessions(self.policy.storage_root)

    def start(self) -> CaptureSession:
        self.policy.authorize_start()
        if not self.backend.available():
            raise RuntimeError("no safe screen capture backend is available")
        if (current := self.status()) and current.state in {
            CaptureState.STARTING,
            CaptureState.RECORDING,
            CaptureState.PAUSED,
            CaptureState.STOPPING,
        }:
            raise RuntimeError("a capture session is already active")
        session = new_session(self.policy.storage_root, uuid4().hex)
        session = self.backend.start(session)
        append_session(self.policy.storage_root, session)
        return session

    def _require_active(self) -> CaptureSession:
        session = self.status()
        if session is None or session.state not in {CaptureState.RECORDING, CaptureState.PAUSED}:
            raise RuntimeError("no active capture session")
        return session

    def pause(self) -> CaptureSession:
        session = self._require_active()
        updated = self.backend.pause(session)
        append_session(self.policy.storage_root, updated)
        return updated

    def resume(self) -> CaptureSession:
        session = self._require_active()
        updated = self.backend.resume(session)
        append_session(self.policy.storage_root, updated)
        return updated

    def stop(self) -> CaptureSession:
        session = self._require_active()
        updated = self.backend.stop(session)
        append_session(self.policy.storage_root, updated)
        return updated
