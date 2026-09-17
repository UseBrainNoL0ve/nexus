"""Portable package-update inspection for common Linux package managers."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence

from nexus.packages.pacman import PackageUpdate
from nexus.platform import PackageBackend, detect_package_backend


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), check=False, capture_output=True, text=True, timeout=30)


def inspect_updates(
    backend: PackageBackend | None = None,
    runner: CommandRunner | None = None,
) -> list[PackageUpdate]:
    """Inspect updates using the detected native package manager."""
    active = backend or detect_package_backend()
    if active is None:
        return []
    result = (runner or _runner)(active.inspect_command)
    if result.returncode not in {0, 1, 100}:
        return []
    return _parse(active.name, result.stdout)


def _parse(manager: str, output: str) -> list[PackageUpdate]:
    updates: list[PackageUpdate] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("Listing...", "Last metadata", "Loading repository")):
            continue

        if manager == "pacman":
            parts = line.split()
            if len(parts) == 4 and parts[2] == "->":
                repo, name = parts[0].split("/", 1) if "/" in parts[0] else ("unknown", parts[0])
                updates.append(PackageUpdate(name, parts[1], parts[3], repo))
            continue

        if manager == "apt":
            # apt list --upgradable format:
            # package/repository version architecture [upgradable from: old]
            if "[upgradable from:" not in line or "/" not in line:
                continue
            package_ref, remainder = line.split(None, 1)
            package_name = package_ref.split("/", 1)[0]
            if not package_name:
                continue
            available_version = remainder.split(None, 1)[0]
            marker = "[upgradable from:"
            current_version = remainder.split(marker, 1)[1].rstrip("] ")
            if available_version and current_version:
                updates.append(PackageUpdate(package_name, current_version, available_version, "apt"))
            continue

        if manager in {"dnf", "yum"}:
            parts = line.split()
            if len(parts) >= 4 and "." in parts[0]:
                updates.append(PackageUpdate(parts[0], parts[1], parts[2], parts[-1]))
            continue

        if manager == "zypper":
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 5 and parts[0].isdigit():
                updates.append(PackageUpdate(parts[1], parts[2], parts[3], "zypper"))
            continue

        if manager == "eopkg":
            parts = line.split()
            if len(parts) >= 3 and "->" in parts:
                index = parts.index("->")
                if index >= 1 and index + 1 < len(parts):
                    updates.append(PackageUpdate(parts[0], parts[index - 1], parts[index + 1], "eopkg"))

    return updates
