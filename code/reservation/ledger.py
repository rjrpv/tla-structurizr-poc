"""Ledger module.

Owns the TLA+ state variables ``sold``, ``rejected`` and ``canceled``.
"""


class Ledger:
    """Records who was sold a ticket, who was rejected, and who canceled."""

    def __init__(self) -> None:
        self.sold = set()
        self.rejected = set()
        self.canceled = set()

    def record_sale(self, customer: str) -> None:
        if customer in self.sold:
            raise RuntimeError(f"{customer} already sold")
        self.sold.add(customer)

    def record_rejection(self, customer: str) -> None:
        if customer in self.rejected:
            raise RuntimeError(f"{customer} already rejected")
        self.rejected.add(customer)

    def move_to_canceled(self, customer: str) -> None:
        """TLA+ ``Cancel(c)``: move a sold customer to canceled."""
        if customer not in self.sold:
            raise RuntimeError(f"{customer} is not sold; cannot cancel")
        self.sold.discard(customer)
        self.canceled.add(customer)

    def answered(self) -> set:
        return self.sold | self.rejected | self.canceled
