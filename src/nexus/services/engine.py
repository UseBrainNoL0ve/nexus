from dataclasses import dataclass
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from nexus.services.actions import ServiceActionProposal
from nexus.services.audit import new_audit_entry, write_audit_entry


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
    audit_path: Path | None = None,
) -> ActionResult:
    """Execute a planned service action only after explicit confirmation.

    Commands are passed as an argument sequence rather than through a shell.
    A caller can inject a runner for deterministic tests without touching the
    real system. When audit_path is supplied, blocked or attempted actions
    are appended to a JSON Lines audit log.
    """
    if not proposal.requires_confirmation:
        raise ValueError("service action proposal must require confirmation")

    def audit(*, confirmed_value: bool, executed_value: bool, result: str, return_code_value=None) -> None:
        if audit_path is None:
            return
        entry = new_audit_entry(
            service=proposal.service,
            action=proposal.action,
            risk=proposal.risk,
            confirmed=confirmed_value,
            executed=executed_value,
            result=result,
            return_code=return_code_value,
        )
        write_audit_entry(entry, audit_path)

    if not confirmed:
        audit(confirmed_value=False, executed_value=False, result="confirmation_required")
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
        audit(confirmed_value=True, executed_value=True, result="execution_error")
        return ActionResult(
            proposal=proposal,
            executed=True,
            return_code=None,
            stdout="",
            stderr=str(exc),
        )

    result = "success" if completed.returncode == 0 else "failed"
    audit(
        confirmed_value=True,
        executed_value=True,
        result=result,
        return_code_value=completed.returncode,
    )
    return ActionResult(
        proposal=proposal,
        executed=True,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
