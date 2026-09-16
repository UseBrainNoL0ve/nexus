from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class ActionSpec:
    id: str
    description: str
    risk: str
    requires_confirmation: bool = True
    capability: str = "system"


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    requires_confirmation: bool


@dataclass(frozen=True)
class ExecutionResult:
    action_id: str
    executed: bool
    status: str
    message: str
    timestamp: str


ActionHandler = Callable[[dict[str, Any]], str]


class ActionRegistry:
    """Allow-list of named actions. There is deliberately no shell API here."""

    def __init__(self) -> None:
        self._specs: dict[str, ActionSpec] = {}
        self._handlers: dict[str, ActionHandler] = {}

    def register(self, spec: ActionSpec, handler: ActionHandler) -> None:
        if spec.id in self._specs:
            raise ValueError(f"duplicate action: {spec.id}")
        if not spec.id or any(char.isspace() for char in spec.id):
            raise ValueError("action id must be non-empty and contain no whitespace")
        self._specs[spec.id] = spec
        self._handlers[spec.id] = handler

    def get(self, action_id: str) -> ActionSpec:
        try:
            return self._specs[action_id]
        except KeyError as exc:
            raise KeyError(f"unknown NEXUS action: {action_id}") from exc

    def handler(self, action_id: str) -> ActionHandler:
        self.get(action_id)
        return self._handlers[action_id]

    def list(self) -> list[ActionSpec]:
        return [self._specs[key] for key in sorted(self._specs)]


class AutomationPolicy:
    """Central authorization boundary for every platform execution."""

    def decide(self, spec: ActionSpec, *, confirmed: bool, dry_run: bool) -> PolicyDecision:
        if dry_run:
            return PolicyDecision(True, "dry-run requested; no mutation will occur", spec.requires_confirmation)
        if spec.requires_confirmation and not confirmed:
            return PolicyDecision(False, "explicit confirmation is required", True)
        return PolicyDecision(True, "action is registered and authorized", spec.requires_confirmation)


class AutomationPlatform:
    def __init__(self, registry: ActionRegistry, audit_path: Path = Path(".nexus/platform-audit.jsonl")) -> None:
        self.registry = registry
        self.policy = AutomationPolicy()
        self.audit_path = audit_path

    def execute(
        self,
        action_id: str,
        parameters: dict[str, Any] | None = None,
        *,
        confirmed: bool = False,
        dry_run: bool = True,
    ) -> ExecutionResult:
        spec = self.registry.get(action_id)
        decision = self.policy.decide(spec, confirmed=confirmed, dry_run=dry_run)
        timestamp = datetime.now(timezone.utc).isoformat()
        if not decision.allowed:
            result = ExecutionResult(action_id, False, "blocked", decision.reason, timestamp)
        elif dry_run:
            result = ExecutionResult(action_id, False, "planned", decision.reason, timestamp)
        else:
            try:
                message = self.registry.handler(action_id)(parameters or {})
            except Exception as exc:  # execution boundary: record failure, don't hide it
                result = ExecutionResult(action_id, True, "failed", str(exc), timestamp)
            else:
                result = ExecutionResult(action_id, True, "success", message, timestamp)
        self._audit(spec, result, parameters or {}, confirmed, dry_run)
        return result

    def _audit(
        self,
        spec: ActionSpec,
        result: ExecutionResult,
        parameters: dict[str, Any],
        confirmed: bool,
        dry_run: bool,
    ) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            **asdict(result),
            "risk": spec.risk,
            "capability": spec.capability,
            "parameters": parameters,
            "confirmed": confirmed,
            "dry_run": dry_run,
        }
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
