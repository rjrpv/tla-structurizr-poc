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

The module layout mirrors the Structurizr containers in
../../structurizr/reservation.dsl (intake, serving, inventory, ledger).
"""

from .system import ReservationSystem

__all__ = ["ReservationSystem"]
