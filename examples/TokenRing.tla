------------------- MODULE TokenRing -------------------
\* Mutual exclusion by a circulating token (the classic token-ring
\* pattern, a close cousin of the dining-philosophers problem).
\*
\* A single token is passed from process to process. A process may enter
\* its critical section *only while it holds the token*, and when it
\* leaves it hands the token to some other process.
\*
\* The canonical property: **mutual exclusion** -- at most one process is
\* in the critical section at a time. The token is the mechanism that
\* makes it true; the invariant is the statement that it works.
\*
\* Run: java -jar tla2tools.jar -workers auto examples/TokenRing
\* ------------------------------------------------------------------
EXTENDS FiniteSets, Integers

CONSTANT Procs

\* holder : the process currently holding the token.
\* inCS   : the set of processes currently in the critical section.
VARIABLES holder, inCS

Init ==
  /\ holder = CHOOSE p \in Procs : TRUE
  /\ inCS   = {}

\* A process holding the token enters the critical section.
Enter(p) ==
  /\ holder = p
  /\ p \notin inCS
  /\ inCS' = inCS \cup {p}
  /\ UNCHANGED holder

\* A process in the critical section leaves and hands the token to some
\* other process (the choice of successor is nondeterministic).
Leave(p) ==
  /\ p \in inCS
  /\ inCS'  = inCS \ {p}
  /\ holder' \in Procs \ {p}

\* The system enters, leaves, or does nothing (stutter).
Next ==
  (\E p \in Procs : Enter(p))
  \lor (\E p \in Procs : Leave(p))
  \lor UNCHANGED <<holder, inCS>>

Spec == Init /\ [][Next]_<<holder, inCS>>

\* Safety: mutual exclusion -- at most one process in the critical
\* section at a time.
MutualExclusion == Cardinality(inCS) <= 1

====================
