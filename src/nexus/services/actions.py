from dataclasses import dataclass
from typing import Literal

from nexus.services.backend import ServiceBackend, detect_service_backend


ServiceAction = Literal["start", "stop", "restart"]
_ALLOWED_ACTIONS: frozenset[str] = frozenset({"start", "stop", "restart"})


@dataclass(frozen=True)
class ServiceActionProposal:
    """A non-executing proposal for a native service-manager action."""

    service: str
    action: ServiceAction
    risk: str
    command: tuple[str, ...]
    rationale: str
    requires_confirmation: bool = True
    manager: str = "unknown"


def _validate_service(service: str, backend: ServiceBackend) -> None:
    if not service or service.isspace():
        raise ValueError("service name must not be empty")
    if any(character.isspace() for character in service):
        raise ValueError("service name must not contain whitespace")
    if service in {".service", "..service"}:
        raise ValueError("service name is invalid")
    if backend.name == "systemd" and not service.endswith(".service"):
        raise ValueError("systemd service name must end with .service")


def plan_service_action(
    service: str,
    action: ServiceAction,
    backend: ServiceBackend | None = None,
) -> ServiceActionProposal:
    """Build a native service-manager proposal without executing it."""
    if action not in _ALLOWED_ACTIONS:
        raise ValueError(f"unsupported service action: {action}")
    active = backend or detect_service_backend()
    if active is None:
        raise RuntimeError("no supported Linux service manager was detected")
    _validate_service(service, active)

    risk = {"start": "medium", "restart": "medium", "stop": "high"}[action]
    rationale = {
        "start": "Starting a service can change system state and background activity.",
        "restart": "Restarting a service can interrupt the service briefly.",
        "stop": "Stopping a service can interrupt functionality that depends on it.",
    }[action]
    return ServiceActionProposal(
        service=service,
        action=action,
        risk=risk,
        command=active.command(action, service),
        rationale=rationale,
        manager=active.name,
    )
