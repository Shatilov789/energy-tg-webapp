"""Structural checks for every registered process, and the graph-resolution rules themselves."""

import pytest

from backend.app.processes.definition import DecisionRequired, ProcessDefinition
from backend.app.processes.registry import PROCESSES

ALL_PROCESSES = list(PROCESSES.values())
IDS = [process.name for process in ALL_PROCESSES]


def _stage_keys(process: ProcessDefinition) -> list[str]:
    return [row[1] for row in process.stages]


def _targets(entry: dict) -> list[str]:
    return [entry[key] for key in ("next", "yes", "no") if key in entry] + list(entry.get("parallel", []))


@pytest.mark.parametrize("process", ALL_PROCESSES, ids=IDS)
def test_every_stage_has_exactly_one_transition(process: ProcessDefinition):
    keys = _stage_keys(process)
    assert len(keys) == len(set(keys))
    assert set(keys) == set(process.transitions)


@pytest.mark.parametrize("process", ALL_PROCESSES, ids=IDS)
def test_no_dangling_targets(process: ProcessDefinition):
    keys = set(_stage_keys(process))
    for stage_key, entry in process.transitions.items():
        assert set(_targets(entry)) <= keys, stage_key


@pytest.mark.parametrize("process", ALL_PROCESSES, ids=IDS)
def test_every_stage_reachable_from_first(process: ProcessDefinition):
    seen: set[str] = set()
    pending = [process.stages[0][1]]
    while pending:
        key = pending.pop()
        if key not in seen:
            seen.add(key)
            pending.extend(_targets(process.transitions[key]))
    assert seen == set(_stage_keys(process))


@pytest.mark.parametrize("process", ALL_PROCESSES, ids=IDS)
def test_decision_flag_matches_graph(process: ProcessDefinition):
    for _, stage_key, _, _, is_decision in process.stages:
        assert is_decision == ("yes" in process.transitions[stage_key]), stage_key


@pytest.mark.parametrize("process", ALL_PROCESSES, ids=IDS)
def test_process_can_end(process: ProcessDefinition):
    assert any("terminal" in entry for entry in process.transitions.values())


def test_stage_keys_are_globally_unique():
    keys = [key for process in ALL_PROCESSES for key in _stage_keys(process)]
    assert len(keys) == len(set(keys))


GRAPH = ProcessDefinition(
    name="graph",
    stages=[],
    transitions={
        "linear": {"next": "end"},
        "branch": {"yes": "linear", "no": "end"},
        "split": {"parallel": ["linear", "end"]},
        "end": {"terminal": "completed"},
    },
)


def test_resolve_next_follows_each_entry_kind():
    assert GRAPH.resolve_next("linear", None) == ["end"]
    assert GRAPH.resolve_next("branch", True) == ["linear"]
    assert GRAPH.resolve_next("branch", False) == ["end"]
    assert GRAPH.resolve_next("split", None) == ["linear", "end"]
    assert GRAPH.resolve_next("end", None) == []


def test_resolve_next_requires_decision_on_branch():
    with pytest.raises(DecisionRequired):
        GRAPH.resolve_next("branch", None)


def test_terminal_status():
    assert GRAPH.terminal_status("end") == "completed"
    assert GRAPH.terminal_status("linear") is None
