"""Ledger module.

Owns the TLA+ state variables ``sold``, ``rejected`` and ``soldCount``.
"""


class Ledger:
    """Records who was sold a ticket and who was rejected."""

    def __init__(self) -> None:
        self.sold = set()
        self.rejected = set()
        self.sold_count = 0

    def record_sale(self, customer: str) -> None:
        if customer in self.sold:
            raise RuntimeError(f"{customer} already sold")
        self.sold.add(customer)
        self.sold_count += 1

    def record_rejection(self, customer: str) -> None:
        if customer in self.rejected:
            raise RuntimeError(f"{customer} already rejected")
        self.rejected.add(customer)

    def answered(self) -> set:
        return self.sold | self.rejected
