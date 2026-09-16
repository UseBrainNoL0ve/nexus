"""Read-only package inspection for pacman-based Linux systems."""

from dataclasses import dataclass
import subprocess
from collections.abc import Callable, Sequence


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


class PackageManagerError(RuntimeError):
    """Raised when pacman cannot provide package information."""


@dataclass(frozen=True)
class PackageUpdate:
    """A package update reported by pacman."""

    name: str
    current_version: str
    available_version: str
    repository: str


def _default_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def inspect_updates(runner: CommandRunner | None = None) -> list[PackageUpdate]:
    """Return available updates without installing or changing packages."""
    active_runner = runner or _default_runner
    try:
        completed = active_runner(("pacman", "-Qu"))
    except (OSError, subprocess.SubprocessError) as exc:
        raise PackageManagerError(f"unable to run pacman: {exc}") from exc

    if completed.returncode not in {0, 1}:
        detail = completed.stderr.strip() or "pacman returned an unexpected exit code"
        raise PackageManagerError(detail)

    updates: list[PackageUpdate] = []
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) != 4 or parts[2] != "->":
            continue

        repository, name = parts[0].split("/", 1) if "/" in parts[0] else ("unknown", parts[0])
        updates.append(
            PackageUpdate(
                name=name,
                current_version=parts[1],
                available_version=parts[3],
                repository=repository,
            )
        )

    return updates
