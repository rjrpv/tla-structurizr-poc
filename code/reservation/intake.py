"""Request Intake module.

Owns the TLA+ state variable ``pending`` and the ``Request(c)`` guard:
a customer may request only if not yet answered.

Intake owns the pending queue and *drives* serving: :meth:`serve_next`
pops the next pending customer and hands it to the serving logic. This
is the ``intake -> serving`` edge in the pydeps dependency graph.
"""

from .serving import ServingLogic


class RequestIntake:
    """Accepts ticket requests, owns the pending queue, and drives serving."""

    def __init__(self, customers: set, serving: ServingLogic) -> None:
        self.customers = set(customers)
        self.serving = serving
        self.pending = set()

    def may_request(self, customer: str, answered: set) -> bool:
        r"""Mirror of the TLA+ guard: ``c \in Customers /\ c \notin answered``."""
        return customer in self.customers and customer not in answered

    def enqueue(self, customer: str) -> None:
        """Add a customer to the pending queue (TLA+ ``Request(c)``)."""
        self.pending.add(customer)

    def serve_next(self, customer: str = None) -> str:
        """Serve a pending customer (TLA+ ``Serve``). Returns 'sold'/'rejected'.

        ``Serve`` in the spec is nondeterministic (``\\E c \\in pending``). By
        default we pick the first pending customer (deterministic); pass a
        specific pending customer to explore a particular choice.
        """
        if customer is None:
            if not self.pending:
                raise RuntimeError("no pending request")
            customer = sorted(self.pending)[0]
        if customer not in self.pending:
            raise RuntimeError(f"{customer} is not pending")
        self.pending.discard(customer)
        return self.serving.serve(customer)
