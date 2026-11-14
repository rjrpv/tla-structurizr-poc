r"""Python mirror of ``examples/Inventory.tla``.

Stock/inventory checking: a warehouse with a stock of items. A shipment
arrives (stock up, capped at capacity) and an order is fulfilled (stock
down, only if there is stock). The invariant is that the stock stays in
``[0, MaxStock]`` — the lower bound is the "no oversell" property.

Mirrors the TLA+ spec exactly:

    Init == stock = MaxStock
    Ship    == stock' = IF stock < MaxStock THEN stock + 1 ELSE stock
    Fulfill == stock > 0 /\ stock' = stock - 1
    StockInRange == 0 <= stock /\ stock <= MaxStock
"""

MAX_STOCK = 4  # from Inventory.cfg


def initial():
    """Init == stock = MaxStock (the warehouse starts full)."""
    return (MAX_STOCK,)


def successors(state):
    """Next: Ship and/or Fulfill (each a single TLA+ step)."""
    (stock,) = state
    out = set()
    # Ship: up, but never past capacity.
    out.add((stock + 1 if stock < MAX_STOCK else stock,))
    # Fulfill: down, only if there is stock (the guard prevents oversell).
    if stock > 0:
        out.add((stock - 1,))
    return [s for s in out]


def invariant(state) -> bool:
    r"""StockInRange == 0 <= stock /\ stock <= MaxStock."""
    (stock,) = state
    return 0 <= stock <= MAX_STOCK
