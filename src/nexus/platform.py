"""Linux distribution and native package-manager capability detection."""

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
    candidates = {
        "pacman": ("pacman", ("pacman", "-Qu"), ("pacman", "-Syu")),
        "apt": ("apt", ("apt", "list", "--upgradable"), ("apt", "upgrade")),
        "dnf": ("dnf", ("dnf", "check-update"), ("dnf", "upgrade")),
        "yum": ("yum", ("yum", "check-update"), ("yum", "update")),
        "zypper": ("zypper", ("zypper", "list-updates"), ("zypper", "update")),
        "apk": ("apk", ("apk", "version", "-l", "<"), ("apk", "upgrade")),
        "xbps": ("xbps-install", ("xbps-install", "-Mun"), ("xbps-install", "-Su")),
        "eopkg": ("eopkg", ("eopkg", "list-upgrades"), ("eopkg", "upgrade")),
    }
    distro = detect_distribution()
    preference = {
        "arch": "pacman", "cachyos": "pacman", "manjaro": "pacman", "endeavouros": "pacman",
        "debian": "apt", "ubuntu": "apt", "linuxmint": "apt", "pop": "apt", "elementary": "apt",
        "fedora": "dnf", "rhel": "dnf", "rocky": "dnf", "almalinux": "dnf", "nobara": "dnf",
        "opensuse": "zypper", "opensuse-tumbleweed": "zypper", "sles": "zypper",
        "alpine": "apk", "void": "xbps", "solus": "eopkg",
    }
    preferred = preference.get(distro.id)
    ordered = ([preferred] if preferred else []) + [name for name in candidates if name != preferred]
    for name in ordered:
        if not name:
            continue
        executable, inspect, update = candidates[name]
        if shutil.which(executable):
            return PackageBackend(name, executable, inspect, update)
    return None


def detect_service_manager() -> str | None:
    """Return the first available native service manager without executing it."""
    if shutil.which("systemctl"):
        return "systemd"
    for name, executable in (("openrc", "rc-service"), ("runit", "sv"), ("s6-rc", "s6-rc"), ("dinit", "dinitctl")):
        if shutil.which(executable):
            return name
    return None
