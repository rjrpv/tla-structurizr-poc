------------------- MODULE ReservationSystem -------------------
\* A small ticket-reservation counter.
\*
\* Behavior modeled here:
\*   - A finite set of customers each requests a ticket at most once.
\*   - The counter keeps a stock of tickets (MaxInventory).
\*   - A pending request is served: if stock remains the ticket is sold,
\*     otherwise the customer is rejected.
\*
\* This is the *behavioral* half of the proof of concept. The matching
\* *architecture* half (who calls whom, where data lives) is the
\* Structurizr model in ../structurizr.
\* ------------------------------------------------------------------
EXTENDS Naturals, FiniteSets

CONSTANTS MaxInventory, Customers

VARIABLES inventory, pending, sold, rejected, soldCount

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
\* ------------------------------------------------------------------

Init ==
  /\ inventory = MaxInventory
  /\ pending   = {}
  /\ sold      = {}
  /\ rejected  = {}
  /\ soldCount = 0

\* A customer who has not yet been answered requests a ticket.
Request(c) ==
  /\ c \in Customers
  /\ c \notin (pending \cup sold \cup rejected)
  /\ pending' = pending \cup {c}
  /\ UNCHANGED <<inventory, sold, rejected, soldCount>>

\* Serve one pending customer (nondeterministically chosen).
\* Sell if stock remains, else reject.
Serve ==
  /\ pending # {}
  /\ \E c \in pending :
      /\ pending' = pending \ {c}
      /\ IF inventory > 0
           THEN /\ inventory' = inventory - 1
                /\ sold'      = sold \cup {c}
                /\ soldCount' = soldCount + 1
                /\ rejected'  = rejected
           ELSE /\ inventory' = inventory
                /\ sold'      = sold
                /\ soldCount' = soldCount
                /\ rejected'  = rejected \cup {c}

\* Stuttering (UNCHANGED VARS) lets the model "stay put" once every
\* customer has been answered, so the finite run terminates cleanly
\* instead of deadlocking, and the liveness property is checkable.
Next ==
  (\E c \in Customers : Request(c))
  \lor Serve
  \lor UNCHANGED <<inventory, pending, sold, rejected, soldCount>>

VARS == <<inventory, pending, sold, rejected, soldCount>>

\* Weak fairness on Serve so the queue cannot be starved forever.
Spec ==
  Init /\ [][Next]_VARS /\ WF_VARS(Serve)

\* ------------------------------------------------------------------
\* Properties to check
\* ------------------------------------------------------------------

\* Safety: stock is never negative (the counter never oversells).
NoOversell == inventory >= 0

\* Safety: at most MaxInventory tickets are ever sold.
BoundedSales == soldCount <= MaxInventory

\* Liveness: the queue eventually drains and stays empty, i.e. every
\* customer who requests is eventually answered (sold or rejected).
Progress == []<>(pending = {})

====================
