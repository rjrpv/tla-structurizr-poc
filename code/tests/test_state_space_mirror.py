"""State-space mirror test: the concrete code explores the same states as TLA+.

This is the strongest "spec mirrors code" check. It performs a breadth-first
search over the *concrete* Python implementation — driving real
``ReservationSystem.request()`` / ``serve()`` / ``cancel()`` calls, exactly as
the TLA+ spec's ``Request`` / ``Serve`` / ``Cancel`` actions fire — and asserts:

  1. Every reachable state satisfies the TLA+ invariants (NoOversell,
     BoundedStock, partition).
  2. The number of distinct reachable states equals the number TLC reported
     for the same model (MaxInventory=2, Customers={alice,bob,carol}):
     **75 distinct states** (see tla/tlc_output.txt).

The TLA+ ``Serve`` is nondeterministic (``\\E c \\in pending``) and ``Cancel``
is (``\\E c \\in sold``), so the search serves *each* pending customer and
cancels *each* sold customer to enumerate all of the model's transitions. If
the concrete code's behavior ever diverges from the abstract model — an extra
transition, a missing guard, a state the spec can't reach — the state count
(or an invariant) will not match and the test fails.
"""

import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reservation import ReservationSystem  # noqa: E402

MAX_INVENTORY = 2
CUSTOMERS = frozenset({"alice", "bob", "carol"})
# From tla/tlc_output.txt: "229 states generated, 75 distinct states found".
EXPECTED_DISTINCT_STATES = 75


def _state_tuple(sys: ReservationSystem):
    s = sys.snapshot()
    return (s["inventory"], s["pending"], s["sold"], s["rejected"], s["canceled"])


def _restore(state) -> ReservationSystem:
    """Rebuild a concrete system in a given state (to explore successors)."""
    inventory, pending, sold, rejected, canceled = state
    sys = ReservationSystem(MAX_INVENTORY, set(CUSTOMERS))
    sys.inventory.stock = inventory
    sys.intake.pending = set(pending)
    sys.ledger.sold = set(sold)
    sys.ledger.rejected = set(rejected)
    sys.ledger.canceled = set(canceled)
    return sys


def _successors(state):
    """Drive the REAL code to compute successors, mirroring the TLA+ Next relation."""
    probe = _restore(state)
    out = []
    # Request(c): c in Customers, c not in pending/sold/rejected/canceled.
    for c in CUSTOMERS:
        if probe.intake.may_request(c, probe.ledger.answered()):
            fresh = _restore(state)
            fresh.request(c)
            out.append(_state_tuple(fresh))
    # Serve: the spec is nondeterministic, so serve EACH pending customer.
    for c in list(probe.intake.pending):
        fresh = _restore(state)
        fresh.serve(c)
        out.append(_state_tuple(fresh))
    # Cancel: the spec is nondeterministic, so cancel EACH sold customer.
    for c in list(probe.ledger.sold):
        fresh = _restore(state)
        fresh.cancel(c)
        out.append(_state_tuple(fresh))
    # (Stuttering UNCHANGED is a self-loop; it adds no new states.)
    return out


def _invariants_hold(state) -> bool:
    inventory, pending, sold, rejected, canceled = state
    return (
        inventory >= 0
        and inventory <= MAX_INVENTORY
        and not (pending & sold)
        and not (pending & rejected)
        and not (pending & canceled)
        and not (sold & rejected)
        and not (sold & canceled)
        and not (rejected & canceled)
    )


def test_concrete_state_space_matches_tla_model():
    initial = (MAX_INVENTORY, frozenset(), frozenset(), frozenset(), frozenset())
    seen = {initial}
    queue = deque([initial])
    while queue:
        state = queue.popleft()
        assert _invariants_hold(state), f"TLA+ invariant violated in reachable state {state}"
        for nxt in _successors(state):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    assert len(seen) == EXPECTED_DISTINCT_STATES, (
        f"concrete code explores {len(seen)} distinct states, "
        f"but the TLA+ model (TLC) explores {EXPECTED_DISTINCT_STATES} — "
        "the code no longer mirrors the spec"
    )


def test_concrete_system_walks_only_valid_states():
    """Drive the real ReservationSystem through a full run with a cancellation;
    every observed state must satisfy the invariants."""
    sys = ReservationSystem(MAX_INVENTORY, set(CUSTOMERS))
    for c in sorted(CUSTOMERS):
        sys.request(c)
    # Serve in a fixed order; carol is rejected (no stock).
    while sys.intake.pending:
        sys.serve(sorted(sys.intake.pending)[0])
    assert _state_tuple(sys) == (0, frozenset(), frozenset({"alice", "bob"}), frozenset({"carol"}), frozenset())
    assert _invariants_hold(_state_tuple(sys))
    # alice cancels: ticket returns to stock, alice moves to canceled.
    sys.cancel("alice")
    assert _state_tuple(sys) == (1, frozenset(), frozenset({"bob"}), frozenset({"carol"}), frozenset({"alice"}))
    assert _invariants_hold(_state_tuple(sys))
