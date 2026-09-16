"""Automation rules and safe action planning."""

from nexus.automation.planner import ActionProposal, plan_actions
from nexus.automation.rules import AutomationRule, RuleResult, evaluate_rules

__all__ = [
    "ActionProposal",
    "AutomationRule",
    "RuleResult",
    "evaluate_rules",
    "plan_actions",
]
