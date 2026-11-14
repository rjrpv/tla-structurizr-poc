"""State-space mirror tests: the concrete code explores the same states as TLA+.

This is the anchor that ties the Python implementations to the TLA+ models.
For each of the eight canonical examples it performs a breadth-first search
over the *concrete* Python mirror — driving the real ``successors()``
transition function, exactly as the TLA+ spec's ``Next`` relation fires — and
asserts two things:

  1. **The TLA+ invariant holds in every reachable state.** The mirror's
     ``invariant()`` is the Python rendering of the TLA+ ``INVARIANT`` line in
     the ``.cfg`` (e.g. ``NoOversell``, ``MutualExclusion``, ``Agreement``).
     If the code ever reaches a state the spec says is illegal, this fails.

  2. **The number of distinct reachable states equals what TLC reported** for
     the same model (see ``examples/tlc_output.txt``). If the concrete code's
     behavior diverges from the abstract model — an extra transition, a missing
     guard, a state the spec can't reach — the count will not match and the
     test fails.

This is the same "spec mirrors code" check the main model uses
(``code/tests/test_state_space_mirror.py``), applied to each canonical
example. The expected counts are read from the TLC run, so the code is checked
against the *actual* state space the model checker found, not a hand-picked
number.
"""

import sys
from collections import deque
from pathlib import Path

import pytest

# Make the example mirrors importable (they live in examples/code/).
CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

import consensus  # noqa: E402
import counter  # noqa: E402
import fifo_queue  # noqa: E402
import inventory  # noqa: E402
import key_value_store  # noqa: E402
import leader_election  # noqa: E402
import token_ring  # noqa: E402
import traffic_light  # noqa: E402

# (display name, mirror module, distinct states TLC reported for the model).
# The counts come from examples/tlc_output.txt, captured from the TLC runs.
EXAMPLES = [
    ("TrafficLight", traffic_light, 2),
    ("Counter", counter, 6),
    ("Queue", fifo_queue, 4),
    ("LeaderElection", leader_election, 4),
    ("TokenRing", token_ring, 6),
    ("Inventory", inventory, 5),
    ("KeyValueStore", key_value_store, 4),
    ("Consensus", consensus, 83),
]


def _explore(module):
    """BFS the concrete mirror; return (reachable states, invariant violations)."""
    start = module.initial()
    seen = {start}
    queue = deque([start])
    violations = []
    while queue:
        state = queue.popleft()
        if not module.invariant(state):
            violations.append(state)
        for nxt in module.successors(state):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen, violations


@pytest.mark.parametrize(
    "name, module, expected",
    EXAMPLES,
    ids=[e[0] for e in EXAMPLES],
)
def test_invariant_holds_in_every_reachable_state(name, module, expected):
    """The TLA+ invariant must hold in every state the code can reach."""
    _, violations = _explore(module)
    assert not violations, (
        f"{name}: the TLA+ invariant is violated in reachable state(s): "
        f"{violations[:3]}{'...' if len(violations) > 3 else ''}"
    )


@pytest.mark.parametrize(
    "name, module, expected",
    EXAMPLES,
    ids=[e[0] for e in EXAMPLES],
)
def test_concrete_state_space_matches_tla_model(name, module, expected):
    """The code must explore exactly the states TLC found for the model."""
    seen, _ = _explore(module)
    assert len(seen) == expected, (
        f"{name}: the concrete code explores {len(seen)} distinct states, "
        f"but the TLA+ model (TLC) explores {expected} — "
        "the code no longer mirrors the spec"
    )
