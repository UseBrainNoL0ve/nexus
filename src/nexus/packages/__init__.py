"""Linux package-manager inspection and safe update planning."""

from nexus.packages.actions import PackageUpdateProposal, plan_package_updates
from nexus.packages.engine import PackageActionResult, execute_package_update
from nexus.packages.generic import inspect_updates
from nexus.packages.pacman import PackageManagerError, PackageUpdate

__all__ = [
    "PackageActionResult",
    "PackageManagerError",
    "PackageUpdate",
    "PackageUpdateProposal",
    "execute_package_update",
    "inspect_updates",
    "plan_package_updates",
]
