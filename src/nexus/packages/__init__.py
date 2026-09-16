"""Linux package manager inspection and safe update planning."""

from nexus.packages.pacman import PackageManagerError, PackageUpdate, inspect_updates

__all__ = ["PackageManagerError", "PackageUpdate", "inspect_updates"]
