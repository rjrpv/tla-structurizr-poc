"""Cancellation module.

Owns the TLA+ ``Cancel(c)`` action: a customer who was sold a ticket
cancels it. The ticket returns to stock and the customer moves from
``sold`` to ``canceled`` (and can no longer request).

This is the new module added by the cancel/refund feature. In the pydeps
dependency graph it points at ``inventory`` (restock) and ``ledger``
(move the customer), and is wired in by ``system``.
"""

from .inventory import Inventory
from .ledger import Ledger


class Cancellation:
    """Handles a sold customer canceling their ticket (TLA+ ``Cancel(c)``)."""

    def __init__(self, inventory: Inventory, ledger: Ledger):
        self.inventory = inventory
        self.ledger = ledger

    def cancel(self, customer: str) -> None:
        """Move ``customer`` from sold to canceled and return a ticket to stock."""
        if customer not in self.ledger.sold:
            raise RuntimeError(f"{customer} has no ticket to cancel")
        self.ledger.move_to_canceled(customer)
        self.inventory.restock_one()
