r"""Python mirror of ``examples/TrafficLight.tla``.

The state is the light's color. Each step flips it. The invariant is that
the light is always one of the two colors.

Mirrors the TLA+ spec exactly:

    Init == light = "green"
    Next == IF light = "green" THEN light' = "red" ELSE light' = "green"
    ValidColor == light \in {"green", "red"}
"""

COLORS = frozenset({"green", "red"})


def initial():
    """Init == light = "green"."""
    return ("green",)


def successors(state):
    """Next: flip the light. Deterministic, so exactly one successor."""
    (light,) = state
    nxt = "red" if light == "green" else "green"
    return [(nxt,)]


def invariant(state) -> bool:
    r"""ValidColor == light \in {"green", "red"}."""
    (light,) = state
    return light in COLORS
