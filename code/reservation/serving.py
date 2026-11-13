"""Serving Logic container.

Implements the TLA+ ``Serve`` decision: given a customer, sell a ticket
if stock remains, else reject. It is a pure decision over the inventory
and ledger — it does not own the queue (that is the intake's job), which
is why its dependencies are ``serving -> inventory`` and
``serving -> ledger`` in the Structurizr model.
"""

from .inventory import Inventory
from .ledger import Ledger


class ServingLogic:
    """Decides whether a served customer is sold a ticket or rejected."""

    def __init__(self, inventory: Inventory, ledger: Ledger):
        self.inventory = inventory
        self.ledger = ledger

    def serve(self, customer: str) -> str:
        """Sell a ticket to ``customer`` if stock remains, else reject. Returns 'sold'/'rejected'."""
        if self.inventory.has_stock():
            self.inventory.sell_one()
            self.ledger.record_sale(customer)
            return "sold"
        self.ledger.record_rejection(customer)
        return "rejected"
