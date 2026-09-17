"""Portable package-update inspection for common Linux package managers."""

from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess
from collections.abc import Callable, Sequence

from nexus.platform import PackageBackend, detect_package_backend


@dataclass(frozen=True)
class GenericPackageUpdate:
    name: str
    current_version: str
    available_version: str
    repository: str


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), check=False, capture_output=True, text=True, timeout=30)


def inspect_updates(backend: PackageBackend | None = None, runner: CommandRunner = _runner) -> list[GenericPackageUpdate]:
    """Inspect updates using the detected native package manager.

    Parsing is deliberately conservative. A manager whose output format is
    not confidently understood returns an empty list rather than inventing
    package versions. The legacy pacman adapter remains available unchanged.
    """
    active = backend or detect_package_backend()
    if active is None:
        return []
    result = runner(active.inspect_command)
    if result.returncode not in {0, 1, 100}:
        return []
    return _parse(active.name, result.stdout)


def _parse(manager: str, output: str) -> list[GenericPackageUpdate]:
    updates: list[GenericPackageUpdate] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith(("Listing...", "Last metadata", "Loading repository")):
            continue
        if manager == "pacman":
            parts = line.split()
            if len(parts) == 4 and parts[2] == "->":
                repo, name = parts[0].split("/", 1) if "/" in parts[0] else ("unknown", parts[0])
                updates.append(GenericPackageUpdate(name, parts[1], parts[3], repo))
        elif manager == "apt":
            match = re.match(r"^([^/\s]+)/[^\s]+\s+([^\s]+)\s+\[upgradable from: ([^\]]+)\]", line)
            if match:
                updates.append(GenericPackageUpdate(match.group(1), match.group(3), match.group(2), "apt"))
        elif manager in {"dnf", "yum"}:
            parts = line.split()
            if len(parts) >= 4 and parts[0] and "." in parts[0]:
                updates.append(GenericPackageUpdate(parts[0], parts[1], parts[1], parts[-1]))
        elif manager == "zypper":
            parts = line.split("|")
            if len(parts) >= 4 and parts[0].strip().isdigit():
                updates.append(GenericPackageUpdate(parts[1].strip(), parts[2].strip(), parts[3].strip(), "zypper"))
        elif manager == "eopkg":
            parts = line.split()
            if len(parts) >= 3 and "->" in parts:
                index = parts.index("->")
                if index >= 1 and index + 1 < len(parts):
                    updates.append(GenericPackageUpdate(parts[0], parts[index - 1], parts[index + 1], "eopkg"))
    return updates
