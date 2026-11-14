------------------- MODULE KeyValueStore -------------------
\* A minimal key-value store: a map from a fixed set of keys to values.
\*
\* The only state-changing operation is Put (a Get just reads the current
\* value, so it is not a step in the model). The canonical property: the
\* store is always *well-formed* -- every key has a value from the
\* allowed value set.
\*
\* This example also shows the EXCEPT operator, the TLA+ way to update
\* one field of a record or function without rewriting the whole thing.
\*
\* Run: java -jar tla2tools.jar -workers auto examples/KeyValueStore
\* ------------------------------------------------------------------
CONSTANT Keys

VARIABLES store

\* Every key starts at value 0.
Init == store = [k \in Keys |-> 0]

\* Put: set key k to value v.
Put(k, v) ==
  /\ store' = [store EXCEPT ![k] = v]

Next ==
  (\E k \in Keys, v \in {0, 1} : Put(k, v))
  \lor UNCHANGED store

Spec == Init /\ [][Next]_store

\* Safety: the store is always well-formed -- a total function from Keys
\* to {0, 1}.
WellFormed == store \in [Keys -> {0, 1}]

====================
