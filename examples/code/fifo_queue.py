r"""Python mirror of ``examples/Queue.tla``.

A bounded FIFO queue. The state is the sequence of items. Enqueue appends
to the tail (if under capacity); dequeue removes the head. The invariant is
that the queue never exceeds its capacity.

Mirrors the TLA+ spec exactly:

    Init == q = <<>>
    Enqueue == Len(q) < MaxSize /\ q' = Append(q, "item")
    Dequeue == Len(q) > 0 /\ q' = Tail(q)
    Bounded == Len(q) <= MaxSize
"""

MAX_SIZE = 3  # from Queue.cfg


def initial():
    """Init == q = <<>>."""
    return ((),)


def successors(state):
    """Next: enqueue (if room) and/or dequeue (if non-empty)."""
    (q,) = state
    out = []
    if len(q) < MAX_SIZE:
        out.append((q + ("item",),))
    if len(q) > 0:
        out.append((q[1:],))
    return out


def invariant(state) -> bool:
    """Bounded == Len(q) <= MaxSize."""
    (q,) = state
    return len(q) <= MAX_SIZE
