"""Property-based tests driven by the TLA+ invariants.

The TLA+ spec (tla/ReservationSystem.tla) declares:

    NoOversell   == inventory >= 0
    BoundedStock == inventory <= MaxInventory
    Progress     == []<>(pending = {})

(There is no longer a ``BoundedSales == soldCount <= MaxInventory``
invariant: with the cancel/refund feature a ticket can be resold, so a
lifetime "ever sold" counter can legitimately exceed ``MaxInventory``. The
bound now lives on the stock itself.)

These tests run the *concrete* Python implementation with randomized
request/serve/cancel interleavings and assert the same invariants hold after
every step — i.e. the code is checked against the properties TLC proved over
the abstract model.
"""

import random
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reservation import ReservationSystem  # noqa: E402


def no_oversell(sys: ReservationSystem) -> bool:
    return sys.inventory.stock >= 0


def bounded_stock(sys: ReservationSystem) -> bool:
    return sys.inventory.stock <= sys.max_inventory


def partition_invariant(sys: ReservationSystem) -> bool:
    """pending, sold, rejected, canceled are disjoint; each customer at most once."""
    s = sys.snapshot()
    buckets = (s["pending"], s["sold"], s["rejected"], s["canceled"])
    for i in range(len(buckets)):
        for j in range(i + 1, len(buckets)):
            if buckets[i] & buckets[j]:
                return False
    return True


@settings(max_examples=200, deadline=None)
@given(
    max_inventory=st.integers(min_value=0, max_value=6),
    customers=st.lists(st.text(min_size=1, max_size=3), min_size=0, max_size=6).map(set),
    actions=st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=60),
)
def test_invariants_hold_under_random_interleaving(max_inventory, customers, actions):
    sys = ReservationSystem(max_inventory, customers)
    rng = random.Random(hash((max_inventory, tuple(sorted(customers)), tuple(actions))) % 2**32)
    for _ in actions:
        # Choose a legal action: request an eligible customer, serve a pending
        # one, or cancel a sold one.
        eligible = [c for c in customers if sys.intake.may_request(c, sys.ledger.answered())]
        pending = list(sys.intake.pending)
        sold = list(sys.ledger.sold)
        moves = []
        if eligible:
            moves.append(("request", rng.choice(eligible)))
        if pending:
            moves.append(("serve", None))
        if sold:
            moves.append(("cancel", rng.choice(sold)))
        if not moves:
            break  # quiescent: nothing to request, serve, or cancel
        kind, arg = moves[rng.randrange(len(moves))]
        if kind == "request":
            sys.request(arg)
        elif kind == "serve":
            sys.serve()
        else:
            sys.cancel(arg)
        # The TLA+ invariants must hold after EVERY step.
        assert no_oversell(sys), f"NoOversell violated: {sys.snapshot()}"
        assert bounded_stock(sys), f"BoundedStock violated: {sys.snapshot()}"
        assert partition_invariant(sys), f"partition violated: {sys.snapshot()}"


@settings(max_examples=200, deadline=None)
@given(
    max_inventory=st.integers(min_value=0, max_value=6),
    customers=st.lists(st.text(min_size=1, max_size=3), min_size=1, max_size=6).map(set),
)
def test_progress_queue_drains(max_inventory, customers):
    """Liveness: if we keep serving until nothing is pending, the queue is empty."""
    sys = ReservationSystem(max_inventory, customers)
    for c in sorted(customers):
        sys.request(c)
    while sys.intake.pending:
        sys.serve()
    assert sys.snapshot()["pending"] == frozenset(), "Progress violated: queue did not drain"


def test_request_then_serve_happy_path():
    sys = ReservationSystem(2, {"alice", "bob", "carol"})
    sys.request("alice")
    assert sys.serve() == "sold"
    assert sys.snapshot() == {
        "inventory": 1,
        "pending": frozenset(),
        "sold": frozenset({"alice"}),
        "rejected": frozenset(),
        "canceled": frozenset(),
    }


def test_oversell_is_prevented():
    """With 2 tickets and 3 customers, exactly 2 are sold and 1 rejected."""
    sys = ReservationSystem(2, {"alice", "bob", "carol"})
    for c in ("alice", "bob", "carol"):
        sys.request(c)
    results = [sys.serve() for _ in range(3)]
    assert sorted(results) == ["rejected", "sold", "sold"]
    assert sys.inventory.stock == 0
    assert no_oversell(sys) and bounded_stock(sys)


def test_cancel_returns_ticket_to_stock():
    """A sold customer cancels: the ticket returns and stock is restored."""
    sys = ReservationSystem(2, {"alice", "bob"})
    sys.request("alice")
    sys.serve()  # alice sold, stock 1
    assert sys.inventory.stock == 1
    sys.cancel("alice")
    assert sys.inventory.stock == 2  # ticket back
    assert sys.snapshot()["canceled"] == frozenset({"alice"})
    assert "alice" not in sys.ledger.sold
    # alice is now canceled and can no longer request.
    with pytest.raises(RuntimeError):
        sys.request("alice")


def test_cancel_requires_a_ticket():
    sys = ReservationSystem(2, {"alice"})
    with pytest.raises(RuntimeError):
        sys.cancel("alice")  # alice never bought a ticket


def test_request_guard_rejects_double_request():
    sys = ReservationSystem(1, {"alice"})
    sys.request("alice")
    sys.serve()
    with pytest.raises(RuntimeError):
        sys.request("alice")  # already answered


def test_serve_requires_pending():
    sys = ReservationSystem(1, {"alice"})
    with pytest.raises(RuntimeError):
        sys.serve()  # alice never requested
