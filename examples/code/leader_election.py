r"""Python mirror of ``examples/LeaderElection.tla``.

The state is the current leader (a process id, or ``"none"``). A process may
declare itself leader; the leader may step down. The invariant is that the
leader is always a known process or ``"none"`` (i.e. at most one leader).

Mirrors the TLA+ spec exactly:

    Init == leader = "none"
    Declare(p) == p \\in Procs /\ leader' = p
    StepDown   == leader # "none" /\ leader' = "none"
    AtMostOneLeader == leader \\in (Procs \\cup {"none"})
"""

PROCS = frozenset({"p1", "p2", "p3"})  # from LeaderElection.cfg


def initial():
    """Init == leader = "none"."""
    return ("none",)


def successors(state):
    """Next: declare any process leader, or step the leader down."""
    (leader,) = state
    out = []
    # Declare(p): p in Procs (nondeterministic over every process).
    for p in sorted(PROCS):
        out.append((p,))
    # StepDown: only if there is a leader.
    if leader != "none":
        out.append(("none",))
    return out


def invariant(state) -> bool:
    r"""AtMostOneLeader == leader \in (Procs \cup {"none"})."""
    (leader,) = state
    return leader in PROCS or leader == "none"
