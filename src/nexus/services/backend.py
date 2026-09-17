"""Command mapping for common Linux service managers."""

from __future__ import annotations

from dataclasses import dataclass
import shutil


@dataclass(frozen=True)
class ServiceBackend:
    name: str

    def command(self, action: str, service: str) -> tuple[str, ...]:
        commands = {
            "systemd": ("systemctl", action, service),
            "openrc": ("rc-service", service.removesuffix(".service"), action),
            "runit": ("sv", action, f"/etc/sv/{service.removesuffix('.service')}"),
            "s6-rc": ("s6-rc", action, service.removesuffix(".service")),
            "dinit": ("dinitctl", action, service.removesuffix(".service")),
        }
        try:
            return commands[self.name]
        except KeyError as exc:
            raise ValueError(f"unsupported service manager: {self.name}") from exc


def detect_service_backend() -> ServiceBackend | None:
    if shutil.which("systemctl"):
        return ServiceBackend("systemd")
    for name, executable in (("openrc", "rc-service"), ("runit", "sv"), ("s6-rc", "s6-rc"), ("dinit", "dinitctl")):
        if shutil.which(executable):
            return ServiceBackend(name)
    return None
