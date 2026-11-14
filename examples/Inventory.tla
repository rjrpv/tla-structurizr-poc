------------------- MODULE Inventory -------------------
\* Stock/inventory checking: a warehouse with a stock of items.
\*
\* Two things happen: a shipment arrives (stock goes up) and an order is
\* fulfilled (stock goes down). The canonical property: **the stock never
\* goes negative** -- you never sell what you do not have.
\*
\* This is the same "no oversell" property as the main ReservationSystem
\* model, stripped of everything else (no customers, no queue, no
\* refunds) so the one property can be seen in isolation.
\*
\* Run: java -jar tla2tools.jar -workers auto examples/Inventory
\* ------------------------------------------------------------------
EXTENDS Naturals

CONSTANT MaxStock

VARIABLES stock

\* The warehouse starts full.
Init == stock = MaxStock

\* A shipment arrives: stock goes up, but never past capacity.
Ship ==
  /\ stock' = IF stock < MaxStock THEN stock + 1 ELSE stock

\* An order is fulfilled: stock goes down, but only if there is stock.
\* (The `stock > 0` guard is what prevents overselling.)
Fulfill ==
  /\ stock > 0
  /\ stock' = stock - 1

Next == Ship \lor Fulfill \lor UNCHANGED stock

Spec == Init /\ [][Next]_stock

\* Safety: the stock is always within [0, MaxStock]. The lower bound is
\* the "no oversell" property; the upper bound says a warehouse cannot
\* hold more than its capacity.
StockInRange == 0 <= stock /\ stock <= MaxStock

====================
