# The Behavioral Half — TLA+

**File:** [`tla/ReservationSystem.tla`](../tla/ReservationSystem.tla)
**Model:** [`tla/ReservationSystem.cfg`](../tla/ReservationSystem.cfg)
**Result:** [`tla/tlc_output.txt`](../tla/tlc_output.txt)

## What TLA+ is

[TLA+](https://lamport.azurewebsites.net/tla/) (Temporal Logic of Actions) is a
formal specification language for **concurrent and distributed systems**. You
write down:

1. **State** — the variables that describe the system at any moment.
2. **Actions** — how the state can change (the allowed transitions).
3. **Properties** — what must be true (invariants) and what must eventually
   happen (liveness).

The **TLC model checker** then exhaustively explores the reachable state space
and either proves the properties hold for *every* behavior, or produces a
**counterexample** — a concrete sequence of steps that breaks a property.

That last point is the whole value: you don't test a few scenarios, you get a
mathematical guarantee over *all* scenarios (within the model's bounds).

## The model

```tla
VARIABLES inventory, pending, sold, rejected, soldCount
```

- `inventory` — tickets in stock (starts at `MaxInventory`).
- `pending` — customers who requested but haven't been answered.
- `sold` / `rejected` — customers answered with a ticket / "sold out".
- `soldCount` — running count of tickets sold (see note below).

Two actions drive the system:

- **`Request(c)`** — a customer not yet answered joins `pending`.
- **`Serve`** — one pending customer is served: sold if `inventory > 0`, else
  rejected. The choice of *which* customer is nondeterministic.

```tla
Next ==
  (\E c \in Customers : Request(c))
  \lor Serve
  \lor UNCHANGED <<inventory, pending, sold, rejected, soldCount>>
```

The `UNCHANGED` disjunct is **stuttering**: it lets the model "stay put" once
every customer has been answered, so the finite run terminates cleanly instead
of deadlocking (see "bugs TLC caught" below).

## The properties

| Property | Kind | Meaning |
|----------|------|---------|
| `NoOversell` | safety | `inventory >= 0` — stock is never negative |
| `BoundedStock` | safety | `inventory <= MaxInventory` — refunds can't overfill the shelf |
| `Progress` | liveness | `[]<>(pending = {})` — the queue eventually drains |

`safety` = "something bad never happens"; `liveness` = "something good
eventually happens". Checking both is what makes this a *real* model check,
not just a state-invariant sweep.

## The model (config)

```
CONSTANT MaxInventory = 2
CONSTANT Customers = {alice, bob, carol}
SPECIFICATION Spec
INVARIANT NoOversell
INVARIANT BoundedStock
PROPERTY Progress
```

A deliberately small model: 2 tickets, 3 customers. TLC explores all 75
reachable states in well under a second.

## Running it

```sh
java -jar tla2tools.jar -workers auto tla/ReservationSystem
```

Output (from `tla/tlc_output.txt`):

```
Model checking completed. No error has been found.
229 states generated, 75 distinct states found, 0 states left on queue.
```

## Bugs TLC caught during development

This is the payoff of formal methods — the model checker found two genuine
modeling mistakes that a human review or a few unit tests would likely have
missed:

1. **Underspecified action.** The first `Request(c)` only assigned
   `pending'`, leaving `inventory`, `sold`, etc. unassigned. TLC reported:
   *"Successor state is not completely specified by action Request … the
   following variables are not assigned: inventory, rejected, sold, soldCount."*
   Fix: add `UNCHANGED <<inventory, sold, rejected, soldCount>>`.

2. **Terminal-state deadlock.** Without the stuttering disjunct, the model
   reached a state where all customers were answered and no action was
   enabled — TLC reported *"Error: Deadlock reached."* Fix: add
   `UNCHANGED <<…>>` to `Next` so the system can quiesce.

3. **Wrong abstraction once tickets can be refunded.** Adding `Cancel(c)`
   (a sold customer cancels; the ticket returns to stock) broke an invariant
   that looked obviously true — `BoundedSales == soldCount <= MaxInventory`.
   TLC found a counterexample with `MaxInventory = 2`: alice sells, cancels
   (ticket back), then carol and bob sell — so **3 sales from 2 tickets** and
   `soldCount = 3 > 2`. The ticket was *reused*, so a lifetime "ever sold"
   counter is the wrong abstraction. Fix: drop `soldCount` and bound the
   stock itself (`NoOversell` + `BoundedStock`), which is the real invariant.

## Environment notes (this sandbox)

A few quirks of the local toolchain that shaped the spec:

- **Single-line module header.** This SANY build's lexer chokes on the
  multi-line header form; the spec uses the standard single-line header
  `------------------- MODULE ReservationSystem -------------------`.
- **`#` (cardinality) unsupported.** This TLC build rejects `#s` as a unary
  operator (parse error; `#(s)` gives a bogus semantic error). The spec
  therefore bounds the stock directly (`inventory <= MaxInventory`) rather
  than reasoning about set cardinality.
- **`SPECIFICATION` is a reserved word.** The spec operator is named `Spec`
  (the conventional name) rather than `SPECIFICATION`.
- **`UNCHANGED VARS`** (bare identifier) failed; the tuple is inlined instead.

None of these affect the *correctness* of the model — they're toolchain
workarounds. The properties and their verification are unaffected.
