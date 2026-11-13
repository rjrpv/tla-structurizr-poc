------------------- MODULE ReservationSystem -------------------
\* A small ticket-reservation counter.
\*
\* Behavior modeled here:
\*   - A finite set of customers each requests a ticket at most once.
\*   - The counter keeps a stock of tickets (MaxInventory).
\*   - A pending request is served: if stock remains the ticket is sold,
\*     otherwise the customer is rejected.
\*   - A sold customer may cancel: the ticket returns to stock and the
\*     customer is marked canceled (and can no longer request).
\*
\* This is the *behavioral* half of the proof of concept. The matching
\* *architecture* half (who calls whom, where data lives) is observed with
\* pydeps over the Python implementation in ../code (see ../docs/comparison.md).
\* ------------------------------------------------------------------
EXTENDS Naturals, FiniteSets

CONSTANTS MaxInventory, Customers

VARIABLES inventory, pending, sold, rejected, canceled

\* ------------------------------------------------------------------
\* Assumptions
\* ------------------------------------------------------------------
\* MaxInventory : a non-negative integer (tickets in stock at start).
\* Customers    : a finite set of customer identifiers.
\*
\* A customer is in exactly one bucket at any time:
\*   pending  : has requested, not yet answered
\*   sold     : answered with a ticket
\*   rejected : answered with "sold out"
\*   canceled : sold a ticket, then canceled it (ticket returned to stock)
\* ------------------------------------------------------------------

Init ==
  /\ inventory = MaxInventory
  /\ pending   = {}
  /\ sold      = {}
  /\ rejected  = {}
  /\ canceled  = {}

\* A customer who has not yet been answered requests a ticket.
Request(c) ==
  /\ c \in Customers
  /\ c \notin (pending \cup sold \cup rejected \cup canceled)
  /\ pending' = pending \cup {c}
  /\ UNCHANGED <<inventory, sold, rejected, canceled>>

\* Serve one pending customer (nondeterministically chosen).
\* Sell if stock remains, else reject.
Serve ==
  /\ pending # {}
  /\ \E c \in pending :
      /\ pending' = pending \ {c}
      /\ IF inventory > 0
           THEN /\ inventory' = inventory - 1
                /\ sold'      = sold \cup {c}
                /\ rejected'  = rejected
                /\ canceled'  = canceled
           ELSE /\ inventory' = inventory
                /\ sold'      = sold
                /\ rejected'  = rejected \cup {c}
                /\ canceled'  = canceled

\* A customer who was sold a ticket cancels it: the ticket returns to
\* stock and the customer moves from `sold` to `canceled`. This is the
\* new behavior added by the cancel/refund feature.
Cancel(c) ==
  /\ c \in sold
  /\ sold'      = sold \ {c}
  /\ canceled'  = canceled \cup {c}
  /\ inventory' = inventory + 1
  /\ UNCHANGED <<pending, rejected>>

\* Stuttering (UNCHANGED VARS) lets the model "stay put" once every
\* customer has been answered, so the finite run terminates cleanly
\* instead of deadlocking, and the liveness property is checkable.
Next ==
  (\E c \in Customers : Request(c))
  \lor Serve
  \lor (\E c \in Customers : Cancel(c))
  \lor UNCHANGED <<inventory, pending, sold, rejected, canceled>>

VARS == <<inventory, pending, sold, rejected, canceled>>

\* Weak fairness on Serve so the queue cannot be starved forever.
Spec ==
  Init /\ [][Next]_VARS /\ WF_VARS(Serve)

\* ------------------------------------------------------------------
\* Properties to check
\* ------------------------------------------------------------------

\* Safety: stock is never negative (the counter never oversells).
NoOversell == inventory >= 0

\* Safety: stock never exceeds capacity (cancellations return tickets, so
\* inventory can grow back up to -- but never past -- MaxInventory).
BoundedStock == inventory <= MaxInventory

\* (The old `BoundedSales == soldCount <= MaxInventory` invariant is gone:
\* with cancellations a ticket can be resold, so a lifetime "ever sold"
\* counter can legitimately exceed MaxInventory. The bound now lives on the
\* stock itself -- NoOversell below and BoundedStock above.)

\* Liveness: the queue eventually drains and stays empty, i.e. every
\* customer who requests is eventually answered (sold or rejected).
Progress == []<>(pending = {})

====================
