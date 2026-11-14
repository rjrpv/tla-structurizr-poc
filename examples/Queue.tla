------------------- MODULE Queue -------------------
\* A bounded FIFO queue: items are enqueued at the tail and dequeued from
\* the head, in order. The canonical "data structure" example.
\*
\* The state is a single variable: the sequence of items currently in the
\* queue. Enqueue appends; dequeue removes the head. The invariant says
\* the queue never holds more than MaxSize items -- the bound that keeps
\* the state space finite.
\*
\* Run: java -jar tla2tools.jar -workers auto examples/Queue
\* ------------------------------------------------------------------
EXTENDS Sequences, FiniteSets, Integers

CONSTANT MaxSize

VARIABLES q

\* The queue starts empty.
Init == q = <<>>

\* Enqueue: add a new item to the tail. The item's value is irrelevant to
\* the structure, so we model it as "some item" (nondeterministic) -- the
\* queue's behavior depends only on *how many* items it holds.
Enqueue ==
  /\ Len(q) < MaxSize
  /\ q' = Append(q, "item")

\* Dequeue: remove the head.
Dequeue ==
  /\ Len(q) > 0
  /\ q' = Tail(q)

\* The queue either enqueues, dequeues, or does nothing (stutter).
Next == Enqueue \lor Dequeue \lor UNCHANGED q

Spec == Init /\ [][Next]_q

\* Safety: the queue never exceeds its capacity.
Bounded == Len(q) <= MaxSize

====================
