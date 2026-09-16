"""Automation rules and safe action planning."""

from nexus.automation.planner import ActionProposal, plan_actions
from nexus.automation.platform import (
    ActionRegistry,
    ActionSpec,
    AutomationPlatform,
    AutomationPolicy,
    ExecutionResult,
    PolicyDecision,
)
from nexus.automation.rules import AutomationRule, RuleResult, evaluate_rules

__all__ = [
    "ActionProposal",
    "ActionRegistry",
    "ActionSpec",
    "AutomationPlatform",
    "AutomationPolicy",
    "AutomationRule",
    "ExecutionResult",
    "PolicyDecision",
    "RuleResult",
    "evaluate_rules",
    "plan_actions",
]
