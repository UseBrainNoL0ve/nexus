"""Linux package manager inspection and safe update planning."""

from nexus.packages.actions import PackageUpdateProposal, plan_package_updates
from nexus.packages.pacman import PackageManagerError, PackageUpdate, inspect_updates

__all__ = [
    "PackageManagerError",
    "PackageUpdate",
    "PackageUpdateProposal",
    "inspect_updates",
    "plan_package_updates",
]
