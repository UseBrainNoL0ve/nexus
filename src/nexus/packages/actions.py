"""Safe planning for package manager updates."""

from dataclasses import dataclass

from nexus.packages.pacman import PackageUpdate


@dataclass(frozen=True)
class PackageUpdateProposal:
    """A package update proposal that does not execute a package change."""

    package: str
    repository: str
    current_version: str
    available_version: str
    risk: str = "medium"
    requires_confirmation: bool = True

    @property
    def command(self) -> tuple[str, ...]:
        """Return the pacman command that would perform this update."""
        return ("sudo", "pacman", "-S", f"{self.repository}/{self.package}")


def plan_package_updates(updates: list[PackageUpdate]) -> list[PackageUpdateProposal]:
    """Convert inspected package updates into explicit, non-executing proposals."""
    return [
        PackageUpdateProposal(
            package=update.name,
            repository=update.repository,
            current_version=update.current_version,
            available_version=update.available_version,
        )
        for update in updates
    ]
