"""Safe planning for package-manager updates across Linux distributions."""

from dataclasses import dataclass

from nexus.packages.pacman import PackageUpdate
from nexus.platform import PackageBackend, detect_package_backend


@dataclass(frozen=True)
class PackageUpdateProposal:
    """A package update proposal that does not execute a package change."""

    package: str
    repository: str
    current_version: str
    available_version: str
    manager: str = "pacman"
    risk: str = "medium"
    requires_confirmation: bool = True

    @property
    def command(self) -> tuple[str, ...]:
        """Return a native command for the detected package manager."""
        commands = {
            "pacman": ("sudo", "pacman", "-S", f"{self.repository}/{self.package}"),
            "apt": ("sudo", "apt", "install", self.package),
            "dnf": ("sudo", "dnf", "upgrade", self.package),
            "yum": ("sudo", "yum", "update", self.package),
            "zypper": ("sudo", "zypper", "update", self.package),
            "apk": ("sudo", "apk", "upgrade", self.package),
            "xbps": ("sudo", "xbps-install", "-Su", self.package),
            "eopkg": ("sudo", "eopkg", "upgrade", self.package),
        }
        try:
            return commands[self.manager]
        except KeyError as exc:
            raise ValueError(f"unsupported package manager: {self.manager}") from exc


def plan_package_updates(
    updates: list[PackageUpdate],
    backend: PackageBackend | None = None,
) -> list[PackageUpdateProposal]:
    """Convert inspected updates into explicit, non-executing proposals."""
    active = backend or detect_package_backend()
    manager = active.name if active else "pacman"
    return [
        PackageUpdateProposal(
            package=update.name,
            repository=update.repository,
            current_version=update.current_version,
            available_version=update.available_version,
            manager=manager,
        )
        for update in updates
    ]
