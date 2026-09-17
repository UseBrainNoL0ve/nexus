"""Linux distribution and native package-manager capability detection.

NEXUS intentionally detects capabilities instead of hard-coding a distro name.
Unknown distributions remain usable for telemetry and diagnosis; unsupported
mutations are surfaced as unavailable capabilities rather than guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True)
class Distribution:
    id: str
    name: str
    version: str
    id_like: tuple[str, ...] = ()


@dataclass(frozen=True)
class PackageBackend:
    name: str
    executable: str
    inspect_command: tuple[str, ...]
    update_command: tuple[str, ...]


def detect_distribution(path: Path = Path("/etc/os-release")) -> Distribution:
    values: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return Distribution("unknown", "Unknown Linux", "")
    for line in text.splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    like = tuple(item for item in values.get("ID_LIKE", "").split() if item)
    return Distribution(values.get("ID", "unknown"), values.get("NAME", values.get("ID", "Unknown Linux")), values.get("VERSION_ID", ""), like)


def detect_package_backend() -> PackageBackend | None:
    candidates = (
        ("pacman", "pacman", ("pacman", "-Qu"), ("pacman", "-Syu")),
        ("apt", "apt", ("apt", "list", "--upgradable"), ("apt", "upgrade")),
        ("dnf", "dnf", ("dnf", "check-update"), ("dnf", "upgrade")),
        ("yum", "yum", ("yum", "check-update"), ("yum", "update")),
        ("zypper", "zypper", ("zypper", "list-updates"), ("zypper", "update")),
        ("apk", "apk", ("apk", "version", "-l", "'<',"), ("apk", "upgrade")),
        ("xbps", "xbps-install", ("xbps-install", "-Mun"), ("xbps-install", "-Su")),
        ("eopkg", "eopkg", ("eopkg", "list-upgrades"), ("eopkg", "upgrade")),
    )
    for name, executable, inspect, update in candidates:
        if shutil.which(executable):
            return PackageBackend(name, executable, inspect, update)
    return None


def detect_service_manager() -> str | None:
    """Return the first available native service manager without executing it."""
    for name in ("systemd", "openrc", "runit", "s6-rc", "dinit"):
        if name == "systemd" and shutil.which("systemctl"):
            return name
        if name != "systemd" and shutil.which(name):
            return name
    return None
