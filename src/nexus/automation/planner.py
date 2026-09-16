from dataclasses import dataclass

from nexus.automation.rules import RuleResult


@dataclass(frozen=True)
class ActionProposal:
    """A proposed action that still requires explicit confirmation."""

    action_id: str
    action: str
    risk: str
    rationale: str
    requires_confirmation: bool = True


def plan_actions(results: list[RuleResult]) -> list[ActionProposal]:
    """Convert triggered rule results into explicit, non-executing proposals."""
    proposals: list[ActionProposal] = []

    for result in results:
        if not result.triggered:
            continue

        if result.action == "propose-cleanup-analysis":
            proposals.append(
                ActionProposal(
                    action_id="cleanup-analysis",
                    action="analyze-cleanup-candidates",
                    risk="low",
                    rationale=result.message,
                )
            )
        elif result.action == "propose-memory-inspection":
            proposals.append(
                ActionProposal(
                    action_id="memory-inspection",
                    action="inspect-memory-processes",
                    risk="low",
                    rationale=result.message,
                )
            )

    return proposals
