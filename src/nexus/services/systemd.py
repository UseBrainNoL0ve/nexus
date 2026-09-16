from dataclasses import dataclass
import subprocess
from collections.abc import Callable, Sequence


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


class SystemdError(RuntimeError):
    """Raised when systemd inspection cannot be completed safely."""


@dataclass(frozen=True)
class ServiceSnapshot:
    """Read-only state for one systemd service unit."""

    unit: str
    load_state: str
    active_state: str
    sub_state: str
    description: str
    enabled_state: str


def _run_systemctl(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )


def _parse_units(output: str) -> dict[str, ServiceSnapshot]:
    services: dict[str, ServiceSnapshot] = {}

    for line in output.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 4 or not parts[0].endswith(".service"):
            continue

        unit, load_state, active_state, sub_state = parts[:4]
        description = parts[4] if len(parts) == 5 else ""
        services[unit] = ServiceSnapshot(
            unit=unit,
            load_state=load_state,
            active_state=active_state,
            sub_state=sub_state,
            description=description,
            enabled_state="unknown",
        )

    return services


def _parse_enabled(output: str) -> dict[str, str]:
    enabled: dict[str, str] = {}

    for line in output.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].endswith(".service"):
            enabled[parts[0]] = parts[1]

    return enabled


def inspect_services(
    runner: CommandRunner = _run_systemctl,
) -> list[ServiceSnapshot]:
    """Inspect systemd services without starting, stopping, or changing anything."""
    units_command = (
        "systemctl",
        "list-units",
        "--type=service",
        "--all",
        "--no-legend",
        "--no-pager",
        "--plain",
    )
    unit_files_command = (
        "systemctl",
        "list-unit-files",
        "--type=service",
        "--no-legend",
        "--no-pager",
    )

    units_result = runner(units_command)
    if units_result.returncode != 0:
        detail = (units_result.stderr or "systemctl list-units failed").strip()
        raise SystemdError(detail)

    enabled_result = runner(unit_files_command)
    if enabled_result.returncode != 0:
        detail = (enabled_result.stderr or "systemctl list-unit-files failed").strip()
        raise SystemdError(detail)

    services = _parse_units(units_result.stdout)
    enabled_states = _parse_enabled(enabled_result.stdout)

    return [
        ServiceSnapshot(
            unit=service.unit,
            load_state=service.load_state,
            active_state=service.active_state,
            sub_state=service.sub_state,
            description=service.description,
            enabled_state=enabled_states.get(service.unit, "unknown"),
        )
        for service in sorted(services.values(), key=lambda item: item.unit)
    ]
