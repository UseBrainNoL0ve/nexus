"""Confirmation-gated execution engine for planned package updates."""

from dataclasses import dataclass
import subprocess
from collections.abc import Callable, Sequence

from nexus.packages.actions import PackageUpdateProposal


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class PackageActionResult:
    """Result of a package update execution attempt."""

    proposal: PackageUpdateProposal
    executed: bool
    return_code: int | None
    stdout: str
    stderr: str


def _default_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )


def execute_package_update(
    proposal: PackageUpdateProposal,
    *,
    confirmed: bool,
    runner: CommandRunner | None = None,
) -> PackageActionResult:
    """Execute one planned update only after explicit confirmation."""
    if not proposal.requires_confirmation:
        raise ValueError("package update proposal must require confirmation")

    if not confirmed:
        return PackageActionResult(
            proposal=proposal,
            executed=False,
            return_code=None,
            stdout="",
            stderr="Confirmation required; package was not changed.",
        )

    active_runner = runner or _default_runner
    try:
        completed = active_runner(proposal.command)
    except (OSError, subprocess.SubprocessError) as exc:
        return PackageActionResult(
            proposal=proposal,
            executed=True,
            return_code=None,
            stdout="",
            stderr=str(exc),
        )

    return PackageActionResult(
        proposal=proposal,
        executed=True,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
