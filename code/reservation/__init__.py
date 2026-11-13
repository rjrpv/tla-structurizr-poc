"""Reference implementation of the ReservationSystem.

Mirrors the TLA+ spec in ../../tla/ReservationSystem.tla:

    TLA+ state variable   ->  Python owner
    ---------------------    --------------------------
    inventory              ->  Inventory.stock
    pending                ->  RequestIntake.pending
    sold / rejected        ->  Ledger.sold / Ledger.rejected
    soldCount              ->  Ledger.sold_count

    TLA+ action           ->  Python method
    ---------------------    --------------------------
    Request(c)             ->  ReservationSystem.request(c)
    Serve                  ->  ReservationSystem.serve(c=None)

The module layout (intake, serving, inventory, ledger) is the unit of
architecture observation: ``code/observe.py`` runs pydeps over it and
diffs the graph against ``code/baseline.json``.
"""

from .system import ReservationSystem

__all__ = ["ReservationSystem"]
