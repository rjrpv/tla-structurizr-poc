r"""Python mirror of ``examples/TokenRing.tla``.

Mutual exclusion by a circulating token. The state is ``(holder, inCS)``: the
process holding the token, and the set of processes in the critical section.
A process holding the token may enter the CS; a process in the CS may leave
and hand the token to some other process.

Mirrors the TLA+ spec exactly:

    Init == holder = CHOOSE p \\in Procs : TRUE /\ inCS = {}
    Enter(p) == holder = p /\ p \\notin inCS /\ inCS' = inCS \\cup {p}
    Leave(p) == p \\in inCS /\ inCS' = inCS \\ {p} /\ holder' \\in Procs \\ {p}
    MutualExclusion == Cardinality(inCS) <= 1
"""

PROCS = frozenset({"p1", "p2", "p3"})  # from TokenRing.cfg


def initial():
    """Init: the first process holds the token; nobody is in the CS."""
    return (min(PROCS), frozenset())


def successors(state):
    """Next: the disjunction of Enter and Leave.

    Each TLA+ step applies exactly one action. Enter(p) requires ``p`` to
    hold the token; Leave(p) requires ``p`` to be in the CS. Because the
    holder is never in the CS (entering makes it the holder, leaving makes
    it the successor), Enter and Leave target disjoint processes, so any
    combined step is reachable by a sequence of single-action steps. We
    therefore enumerate the single-action successors, which matches TLC's
    state space exactly. Stuttering adds no new states.
    """
    holder, inCS = state
    out = set()
    # Enter(p): p holds the token and is not already in the CS.
    if holder not in inCS:
        out.add((holder, inCS | {holder}))
    # Leave(p): p is in the CS; it leaves and hands the token to another.
    for p in sorted(inCS):
        for h in sorted(PROCS - {p}):
            out.add((h, inCS - {p}))
    return [s for s in out]


def invariant(state) -> bool:
    """MutualExclusion == Cardinality(inCS) <= 1."""
    _, inCS = state
    return len(inCS) <= 1
