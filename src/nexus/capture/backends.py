from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class PortalCapability:
    """Detected prerequisites for the XDG Desktop Portal ScreenCast path."""

    session_type: str
    portal_available: bool
    gdbus_available: bool

    @property
    def available(self) -> bool:
        return self.session_type == "wayland" and self.portal_available and self.gdbus_available


def detect_portal_capability(
    environ: dict[str, str] | None = None,
    which=shutil.which,
    runner=subprocess.run,
) -> PortalCapability:
    """Probe the safe Wayland capture prerequisites without starting a capture."""
    env = environ if environ is not None else os.environ
    session_type = env.get("XDG_SESSION_TYPE", "").lower()
    gdbus_available = which("gdbus") is not None
    if not gdbus_available or session_type != "wayland":
        return PortalCapability(session_type, False, gdbus_available)

    try:
        result = runner(
            [
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.freedesktop.portal.Desktop",
                "--object-path",
                "/org/freedesktop/portal/desktop",
                "--method",
                "org.freedesktop.DBus.Peer.Ping",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return PortalCapability(session_type, False, gdbus_available)
    return PortalCapability(session_type, result.returncode == 0, gdbus_available)


class WaylandPortalBackend:
    """Capability-aware foundation for XDG Portal + PipeWire capture.

    The portal backend deliberately does not claim to record until the PipeWire
    stream consumer is implemented. This prevents a false-positive capture
    state and keeps the fail-closed safety contract intact.
    """

    name = "wayland-portal"

    def __init__(self, capability: PortalCapability | None = None) -> None:
        self.capability = capability or detect_portal_capability()

    def available(self) -> bool:
        return self.capability.available

    def start(self, session):
        raise RuntimeError(
            "Wayland portal detected, but PipeWire stream recording is not implemented yet"
        )

    def pause(self, session):
        raise RuntimeError("Wayland portal capture pause is not implemented yet")

    def resume(self, session):
        raise RuntimeError("Wayland portal capture resume is not implemented yet")

    def stop(self, session):
        raise RuntimeError("Wayland portal capture stop is not implemented yet")
