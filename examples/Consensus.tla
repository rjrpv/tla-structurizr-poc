------------------- MODULE Consensus -------------------
\* A minimal voting consensus: each process votes 0 or 1; once everyone
\* has voted, each process decides the *majority* value.
\*
\* The canonical property of consensus: **agreement** -- all processes
\* decide the same value. With an odd number of processes and a strict
\* majority, the majority value is unique, so agreement holds.
\*
\* (A real consensus protocol -- Paxos, Raft -- also handles failures and
\* guarantees validity and termination; this model isolates *agreement*,
\* the property they all share.)
\*
\* Run: java -jar tla2tools.jar -workers auto examples/Consensus
\* ------------------------------------------------------------------
EXTENDS FiniteSets, Integers

CONSTANT Procs

\* votes   : each process's vote -- -1 until it votes, then 0 or 1.
\* decided : each process's decision -- -1 until it decides, then 0 or 1.
\* (Integer sentinels keep every value the same type, which TLC needs.)
VARIABLES votes, decided

Init ==
  /\ votes   = [p \in Procs |-> -1]
  /\ decided = [p \in Procs |-> -1]

\* A process votes 0 or 1 (once).
Vote(p, v) ==
  /\ votes[p] = -1
  /\ v \in {0, 1}
  /\ votes' = [votes EXCEPT ![p] = v]
  /\ UNCHANGED decided

\* A process decides the majority value, once everyone has voted. The
\* existential picks the unique strict-majority value (there is exactly
\* one, since Procs is odd and everyone has voted). For the 3-process
\* model in the .cfg, "majority" means "more than 1".
Decide(p) ==
  /\ \A q \in Procs : votes[q] # -1
  /\ decided[p] = -1
  /\ \E v \in {0, 1} :
       /\ Cardinality({q \in Procs : votes[q] = v}) > 1
       /\ decided' = [decided EXCEPT ![p] = v]
  /\ UNCHANGED votes

Next ==
  (\E p \in Procs, v \in {0, 1} : Vote(p, v))
  \lor (\E p \in Procs : Decide(p))
  \lor UNCHANGED <<votes, decided>>

Spec == Init /\ [][Next]_<<votes, decided>>

\* Agreement: all processes decide the same value. There is a single
\* value v such that every process's decision is either v or still -1
\* (not yet decided).
Agreement ==
  \E v \in {0, 1} : \A p \in Procs : decided[p] \in {v, -1}

====================
