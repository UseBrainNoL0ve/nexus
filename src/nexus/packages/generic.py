"""Portable package-update inspection for common Linux package managers."""

from __future__ import annotations

import re
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
    """Inspect updates using the detected native package manager.

    The runner is resolved at call time so tests can reliably inject a fake
    command runner without depending on import-time default binding.
    """
    active = backend or detect_package_backend()
    if active is None:
        return []
    active_runner = runner or _runner
    result = active_runner(active.inspect_command)
    if result.returncode not in {0, 1, 100}:
        return []
    return _parse(active.name, result.stdout)


def _parse(manager: str, output: str) -> list[PackageUpdate]:
    updates: list[PackageUpdate] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith(("Listing...", "Last metadata", "Loading repository")):
            continue
        if manager == "pacman":
            parts = line.split()
            if len(parts) == 4 and parts[2] == "->":
                repo, name = parts[0].split("/", 1) if "/" in parts[0] else ("unknown", parts[0])
                updates.append(PackageUpdate(name, parts[1], parts[3], repo))
        elif manager == "apt":
            match = re.match(r"^([^/\s]+)/[^\s]+\s+([^\s]+)\s+\[upgradable from: ([^\]]+)\]", line)
            if match:
                updates.append(PackageUpdate(match.group(1), match.group(3), match.group(2), "apt"))
        elif manager in {"dnf", "yum"}:
            parts = line.split()
            if len(parts) >= 4 and "." in parts[0]:
                updates.append(PackageUpdate(parts[0], parts[1], parts[2], parts[-1]))
        elif manager == "zypper":
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 5 and parts[0].isdigit():
                updates.append(PackageUpdate(parts[1], parts[2], parts[3], "zypper"))
        elif manager == "eopkg":
            parts = line.split()
            if len(parts) >= 3 and "->" in parts:
                index = parts.index("->")
                if index >= 1 and index + 1 < len(parts):
                    updates.append(PackageUpdate(parts[0], parts[index - 1], parts[index + 1], "eopkg"))
    return updates
