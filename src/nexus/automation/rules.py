from dataclasses import dataclass
from typing import Callable

from nexus.core.models import SystemSnapshot


@dataclass(frozen=True)
class RuleResult:
    """Result of evaluating one automation rule."""

    rule: str
    triggered: bool
    message: str
    action: str


@dataclass(frozen=True)
class AutomationRule:
    """A read-only rule that proposes an action without executing it."""

    name: str
    condition: Callable[[SystemSnapshot], bool]
    message: str
    action: str


def default_rules() -> tuple[AutomationRule, ...]:
    """Return the initial safe, observation-only automation rules."""
    return (
        AutomationRule(
            name="disk-pressure",
            condition=lambda snapshot: snapshot.disk.used_percent >= 85.0,
            message="Root filesystem usage is at or above 85%.",
            action="propose-cleanup-analysis",
        ),
        AutomationRule(
            name="memory-pressure",
            condition=lambda snapshot: snapshot.memory.used_percent >= 90.0,
            message="Memory usage is at or above 90%.",
            action="propose-memory-inspection",
        ),
    )


def evaluate_rules(
    snapshot: SystemSnapshot,
    rules: tuple[AutomationRule, ...] | None = None,
) -> list[RuleResult]:
    """Evaluate rules and return proposals; no system mutation occurs."""
    active_rules = rules if rules is not None else default_rules()
    return [
        RuleResult(
            rule=rule.name,
            triggered=rule.condition(snapshot),
            message=rule.message,
            action=rule.action,
        )
        for rule in active_rules
    ]
