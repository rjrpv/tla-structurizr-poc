------------------- MODULE Counter -------------------
\* A saturating counter: it increments up to a cap, then holds.
\*
\* The point: a counter that incremented *forever* has an infinite state
\* space, which TLC cannot check. Capping it at MaxCount makes the state
\* space finite (MaxCount + 1 states) -- and the invariant Bounded is the
\* property that says the cap is respected.
\*
\* This is the core discipline of model checking: the model must be small
\* enough to explore, and the invariant must be strong enough to keep it
\* small.
\*
\* Run: java -jar tla2tools.jar -workers auto examples/Counter
\* ------------------------------------------------------------------
EXTENDS Naturals

CONSTANT MaxCount

VARIABLES count

\* The counter starts at zero.
Init == count = 0

\* Each step adds one, but never past the cap.
Next ==
  /\ count' = IF count < MaxCount THEN count + 1 ELSE count

Spec == Init /\ [][Next]_count

\* Safety: the counter never exceeds MaxCount.
Bounded == count <= MaxCount

====================
