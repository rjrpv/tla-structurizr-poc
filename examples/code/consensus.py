r"""Python mirror of ``examples/Consensus.tla``.

A minimal voting consensus: each process votes 0 or 1; once everyone has
voted, each process decides the *majority* value. The invariant is
**agreement** — all processes decide the same value.

Mirrors the TLA+ spec exactly (integer sentinels: ``-1`` = not yet):

    Init == votes = [p |-> -1] /\ decided = [p |-> -1]
    Vote(p, v)   == votes[p] = -1 /\ v \\in {0,1}
                    /\ votes' = [votes EXCEPT ![p] = v]
    Decide(p)    == (\\A q : votes[q] # -1) /\ decided[p] = -1
                    /\ (\\E v : |{q : votes[q]=v}| > 1) /\ decided' = [..![p]=v]
    Agreement    == (\\E v \\in {0,1} : \\A p : decided[p] \\in {v, -1})
"""

from collections import Counter

PROCS = frozenset({"p1", "p2", "p3"})  # from Consensus.cfg


def initial():
    """Init: nobody has voted or decided yet."""
    votes = frozenset((p, -1) for p in sorted(PROCS))
    decided = frozenset((p, -1) for p in sorted(PROCS))
    return (votes, decided)


def successors(state):
    """Next: Vote(p, v) and Decide(p) (each a single TLA+ step)."""
    votes, decided = dict(state[0]), dict(state[1])
    out = set()

    # Vote(p, v): p has not voted yet; it votes 0 or 1.
    for p in sorted(PROCS):
        if votes[p] == -1:
            for v in (0, 1):
                new_votes = dict(votes)
                new_votes[p] = v
                out.add((frozenset(new_votes.items()), frozenset(decided.items())))

    # Decide(p): everyone has voted and p has not decided; p decides the
    # unique strict-majority value.
    if all(votes[q] != -1 for q in PROCS):
        tally = Counter(votes.values())
        majority = [v for v in (0, 1) if tally.get(v, 0) > 1]
        if len(majority) == 1:
            m = majority[0]
            for p in sorted(PROCS):
                if decided[p] == -1:
                    new_decided = dict(decided)
                    new_decided[p] = m
                    out.add((frozenset(votes.items()), frozenset(new_decided.items())))

    return [s for s in out]


def invariant(state) -> bool:
    """Agreement: all decisions are the same value (or still undecided)."""
    _, decided_items = state
    decided = dict(decided_items)
    for v in (0, 1):
        if all(decided[p] in (v, -1) for p in PROCS):
            return True
    return False
