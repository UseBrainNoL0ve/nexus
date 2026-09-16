from dataclasses import dataclass
from typing import Literal


ServiceAction = Literal["start", "stop", "restart"]
_ALLOWED_ACTIONS: frozenset[str] = frozenset({"start", "stop", "restart"})


@dataclass(frozen=True)
class ServiceActionProposal:
    """A non-executing proposal for a systemd service action."""

    service: str
    action: ServiceAction
    risk: str
    command: tuple[str, ...]
    rationale: str
    requires_confirmation: bool = True


def _validate_service(service: str) -> None:
    if not service or service.isspace():
        raise ValueError("service name must not be empty")
    if any(character.isspace() for character in service):
        raise ValueError("service name must not contain whitespace")
    if not service.endswith(".service"):
        raise ValueError("service name must end with .service")
    if service in {".service", "..service"}:
        raise ValueError("service name is invalid")


def plan_service_action(service: str, action: ServiceAction) -> ServiceActionProposal:
    """Build a systemctl action proposal without executing it."""
    _validate_service(service)
    if action not in _ALLOWED_ACTIONS:
        raise ValueError(f"unsupported service action: {action}")

    risk = {
        "start": "medium",
        "restart": "medium",
        "stop": "high",
    }[action]
    rationale = {
        "start": "Starting a service can change system state and background activity.",
        "restart": "Restarting a service can interrupt the service briefly.",
        "stop": "Stopping a service can interrupt functionality that depends on it.",
    }[action]

    return ServiceActionProposal(
        service=service,
        action=action,
        risk=risk,
        command=("systemctl", action, service),
        rationale=rationale,
    )
