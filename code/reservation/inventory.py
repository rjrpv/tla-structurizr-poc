"""Inventory module.

Owns the TLA+ state variable ``inventory`` (tickets in stock).
"""


class Inventory:
    """Tracks the number of tickets in stock (MaxInventory)."""

    def __init__(self, max_inventory: int):
        if max_inventory < 0:
            raise ValueError("max_inventory must be >= 0")
        self.max_inventory = max_inventory
        self.stock = max_inventory

    def has_stock(self) -> bool:
        return self.stock > 0

    def sell_one(self) -> None:
        if not self.has_stock():
            raise RuntimeError("cannot sell: no stock")
        self.stock -= 1

    def restock_one(self) -> None:
        """Return a ticket to stock (TLA+ ``Cancel``: inventory' = inventory + 1)."""
        if self.stock >= self.max_inventory:
            raise RuntimeError("cannot restock: stock already at capacity")
        self.stock += 1
