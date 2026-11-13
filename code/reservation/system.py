"""ReservationSystem: wires the four containers together.

Dependency direction (matches structurizr/reservation.dsl):

    intake -> serving -> inventory
                       -> ledger

The public API mirrors the TLA+ actions:

    Request(c)  ->  request(c)
    Serve       ->  serve()

``snapshot()`` returns the TLA+ state as a dict so tests can compare it
against the model and check the invariants.
"""

from .inventory import Inventory
from .intake import RequestIntake
from .ledger import Ledger
from .serving import ServingLogic


class ReservationSystem:
    """A small ticket-reservation counter (see tla/ReservationSystem.tla)."""

    def __init__(self, max_inventory: int, customers):
        self.customers = set(customers)
        self.inventory = Inventory(max_inventory)
        self.ledger = Ledger()
        self.serving = ServingLogic(self.inventory, self.ledger)
        self.intake = RequestIntake(self.customers, self.serving)

    # -- TLA+ Request(c) -------------------------------------------------
    def request(self, customer: str) -> None:
        if not self.intake.may_request(customer, self.ledger.answered()):
            raise RuntimeError(f"{customer} may not request (unknown or already answered)")
        self.intake.enqueue(customer)

    # -- TLA+ Serve ------------------------------------------------------
    def serve(self, customer: str = None) -> str:
        if customer is None and not self.intake.pending:
            raise RuntimeError("no pending request to serve")
        return self.intake.serve_next(customer)

    # -- state -----------------------------------------------------------
    def snapshot(self) -> dict:
        """The TLA+ state as a dict (for invariant checks / model mirroring)."""
        return {
            "inventory": self.inventory.stock,
            "pending": frozenset(self.intake.pending),
            "sold": frozenset(self.ledger.sold),
            "rejected": frozenset(self.ledger.rejected),
            "soldCount": self.ledger.sold_count,
        }

    @property
    def max_inventory(self) -> int:
        return self.inventory.max_inventory
