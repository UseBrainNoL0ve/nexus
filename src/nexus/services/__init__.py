"""Linux service inspection and safe action planning."""

from nexus.services.actions import ServiceActionProposal, plan_service_action
from nexus.services.audit import AuditEntry, new_audit_entry, read_audit_entries, write_audit_entry
from nexus.services.engine import ActionResult, execute_service_action
from nexus.services.systemd import ServiceSnapshot, SystemdError, inspect_services

__all__ = [
    "ActionResult",
    "AuditEntry",
    "ServiceActionProposal",
    "ServiceSnapshot",
    "SystemdError",
    "execute_service_action",
    "inspect_services",
    "new_audit_entry",
    "plan_service_action",
    "read_audit_entries",
    "write_audit_entry",
]
