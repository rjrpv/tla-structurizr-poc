"""Python mirror of ``examples/Counter.tla``.

A saturating counter: increments up to ``MAX_COUNT``, then holds. The
invariant is that the counter never exceeds the cap.

Mirrors the TLA+ spec exactly:

    Init == count = 0
    Next == count' = IF count < MaxCount THEN count + 1 ELSE count
    Bounded == count <= MaxCount
"""

MAX_COUNT = 5  # from Counter.cfg


def initial():
    """Init == count = 0."""
    return (0,)


def successors(state):
    """Next: add one, but never past the cap. Deterministic."""
    (count,) = state
    nxt = count + 1 if count < MAX_COUNT else count
    return [(nxt,)]


def invariant(state) -> bool:
    """Bounded == count <= MaxCount."""
    (count,) = state
    return count <= MAX_COUNT
