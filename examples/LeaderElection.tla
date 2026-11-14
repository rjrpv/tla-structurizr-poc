------------------- MODULE LeaderElection -------------------
\* A minimal leader election among a set of processes.
\*
\* Each process has a unique id. A process may *declare* itself leader.
\* The canonical property of any leader election: **at most one leader at
\* a time** (safety -- "at-most-one"). A real protocol (Raft, Paxos,
\* bully) adds the machinery to *reach* a leader (liveness) and to
\* tolerate failures; this model isolates the safety property that all of
\* them must satisfy.
\*
\* Run: java -jar tla2tools.jar -workers auto examples/LeaderElection
\* ------------------------------------------------------------------
EXTENDS FiniteSets

CONSTANT Procs

VARIABLES leader

\* No leader yet (the value "none" means "no leader").
Init == leader = "none"

\* A process declares itself leader.
Declare(p) ==
  /\ p \in Procs
  /\ leader' = p

\* The current leader steps down (e.g. on failure or a new term).
StepDown ==
  /\ leader # "none"
  /\ leader' = "none"

\* The system either elects a leader, steps the leader down, or does
\* nothing (stutter).
Next ==
  (\E p \in Procs : Declare(p))
  \lor StepDown
  \lor UNCHANGED leader

Spec == Init /\ [][Next]_leader

\* Safety: there is at most one leader. Because `leader` holds a single
\* value (or "none"), this holds trivially -- but writing it down is the
\* whole point: it is the property every real election protocol must
\* preserve, and it is the property a broken protocol would violate.
AtMostOneLeader == leader \in (Procs \cup {"none"})

====================
