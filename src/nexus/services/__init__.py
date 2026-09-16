"""Read-only Linux service inspection."""

from nexus.services.systemd import ServiceSnapshot, SystemdError, inspect_services

__all__ = ["ServiceSnapshot", "SystemdError", "inspect_services"]
