from dataclasses import dataclass
import subprocess
from collections.abc import Callable, Sequence

from nexus.services.actions import ServiceActionProposal


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ActionResult:
    """Outcome of an explicitly confirmed service action."""

    proposal: ServiceActionProposal
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
        timeout=30,
    )


def execute_service_action(
    proposal: ServiceActionProposal,
    *,
    confirmed: bool,
    runner: CommandRunner | None = None,
) -> ActionResult:
    """Execute a planned service action only after explicit confirmation.

    Commands are passed as an argument sequence rather than through a shell.
    A caller can inject a runner for deterministic tests without touching the
    real system.
    """
    if not proposal.requires_confirmation:
        raise ValueError("service action proposal must require confirmation")

    if not confirmed:
        return ActionResult(
            proposal=proposal,
            executed=False,
            return_code=None,
            stdout="",
            stderr="Confirmation required; action was not executed.",
        )

    active_runner = runner or _default_runner
    try:
        completed = active_runner(proposal.command)
    except (OSError, subprocess.SubprocessError) as exc:
        return ActionResult(
            proposal=proposal,
            executed=True,
            return_code=None,
            stdout="",
            stderr=str(exc),
        )

    return ActionResult(
        proposal=proposal,
        executed=True,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
