r"""Python mirror of ``examples/KeyValueStore.tla``.

A minimal key-value store: a map from a fixed set of keys to values. The
only step is Put (Get just reads, so it is not a step). The invariant is
that the store is always well-formed — a total function from Keys to
{0, 1}.

Mirrors the TLA+ spec exactly:

    Init == store = [k \\in Keys |-> 0]
    Put(k, v) == store' = [store EXCEPT ![k] = v]
    WellFormed == store \\in [Keys -> {0, 1}]
"""

KEYS = frozenset({"a", "b"})  # from KeyValueStore.cfg
VALUES = (0, 1)


def initial():
    """Init: every key starts at value 0."""
    return (frozenset((k, 0) for k in sorted(KEYS)),)


def successors(state):
    """Next: Put(k, v) for every key and value (nondeterministic)."""
    (store,) = state
    out = set()
    for k in sorted(KEYS):
        for v in VALUES:
            new = dict(store)
            new[k] = v  # the EXCEPT operator, in Python
            out.add((frozenset(new.items()),))
    return [s for s in out]


def invariant(state) -> bool:
    """WellFormed: a total function from Keys to {0, 1}."""
    (items,) = state
    store = dict(items)
    return set(store) == KEYS and all(v in VALUES for v in store.values())
