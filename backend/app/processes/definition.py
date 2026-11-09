"""Declarative shape of a business process: its stage catalog and transition graph.

Each entry in ``ProcessDefinition.transitions``, keyed by stage_key, is one of:

- ``{"next": stage_key}``                  unconditional single successor
- ``{"yes": stage_key, "no": stage_key}``  decision stage, branches on DealStageProgress.decision
- ``{"parallel": [stage_key, ...]}``       fan-out into several concurrent branches
- ``{"terminal": "closed" | "completed"}`` reaching this stage ends the deal

A decision whose two branches converge still points both "yes" and "no" at the same stage, so
the decision is recorded for history. Loops point back at an earlier stage (or at the stage
itself); DealStageProgress has no unique(deal_id, stage_id), so every visit is a new row.
"""

from dataclasses import dataclass, field

# (display_code, stage_key, name, role_owner, is_decision)
StageRow = tuple[str, str, str, str, bool]


class DecisionRequired(Exception):
    """The stage branches on a decision, but none was supplied."""


@dataclass(frozen=True)
class ProcessDefinition:
    """One business process. Stages are listed in display order; the first one starts a deal."""

    name: str
    stages: list[StageRow]
    transitions: dict[str, dict]
    # stage_key -> (yes_label, no_label), for decisions that are not a plain yes/no question.
    decision_labels: dict[str, tuple[str, str]] = field(default_factory=dict)

    def resolve_next(self, stage_key: str, decision: bool | None) -> list[str]:
        """Return the stage_keys that follow a completed stage."""
        entry = self.transitions[stage_key]
        if "parallel" in entry:
            return list(entry["parallel"])
        if "yes" in entry or "no" in entry:
            if decision is None:
                raise DecisionRequired(stage_key)
            return [entry["yes"] if decision else entry["no"]]
        if "terminal" in entry:
            return []
        return [entry["next"]]

    def terminal_status(self, stage_key: str) -> str | None:
        """Return "closed" or "completed" if the stage ends the deal, otherwise None."""
        return self.transitions[stage_key].get("terminal")
