------------------- MODULE TrafficLight -------------------
\* The simplest possible TLA+ model: a traffic light cycling
\* green -> red -> green -> ... forever.
\*
\* The point of this example is the *shape* of every TLA+ model:
\*   VARIABLES   -- the state (what the system looks like at any moment)
\*   Init        -- the initial state
\*   Next        -- the allowed steps (how the state may change)
\*   Spec        -- all behaviors of the system
\*   INVARIANT   -- a property that must hold in every reachable state
\*
\* Run: java -jar tla2tools.jar -workers auto examples/TrafficLight
\* ------------------------------------------------------------------
VARIABLES light

\* The light starts green.
Init == light = "green"

\* Each step flips the light.
Next ==
  /\ IF light = "green" THEN light' = "red"
     ELSE light' = "green"

\* All behaviors of the system, from Init, taking Next steps forever.
Spec == Init /\ [][Next]_light

\* Safety: the light is always one of the two colors -- it can never be
\* in some third, impossible state.
ValidColor == light \in {"green", "red"}

====================
