# Making the Spec Mirror the Code

This is the follow-up to [comparison.md](comparison.md). The PoC showed TLA+ and
pydeps describing the *same* system at two abstractions. This document closes
the loop: it adds a **Python reference implementation** and a set of **tests
that check the code against the spec**, so the "mirror" is enforced by the
build rather than by convention.

The guiding idea: **the spec is the source of truth; the code is a candidate
implementation; the tests are the bridge that proves the candidate matches.**
For structure, the mode is *observation*, not control: pydeps reveals the
code's dependency graph and a committed baseline records what we last saw.

## What was added

```
code/
├── reservation/                 # the reference implementation
│   ├── system.py                # ReservationSystem — wires the modules
│   ├── intake.py                # RequestIntake  (owns `pending`)
│   ├── serving.py               # ServingLogic   (the sell/reject decision)
│   ├── inventory.py             # Inventory      (owns `inventory`)
│   ├── ledger.py                # Ledger         (owns `sold`/`rejected`/`canceled`)
│   └── cancellation.py          # Cancellation   (cancel/refund; restocks)
├── tests/
│   ├── test_invariants.py       # property-based: TLA+ invariants on the code
│   ├── test_state_space_mirror.py  # BFS the code; assert 75 states == TLC
│   └── test_architecture.py     # well-formedness: no cycles + baseline in sync
├── observe.py                   # pydeps observer + acceptance gate
├── baseline.json                # the committed dependency graph (the accepted state)
└── requirements.txt
```

## The bridges

### 1. Behavior: TLA+ invariants → property-based tests

The TLA+ spec declares `NoOversell`, `BoundedStock`, and `Progress`.
`tests/test_invariants.py` runs the *concrete* Python code with randomized
request/serve/cancel interleavings (Hypothesis) and asserts the **same
invariants hold after every step**:

```python
assert sys.inventory.stock >= 0                      # NoOversell
assert sys.inventory.stock <= sys.max_inventory      # BoundedStock
```

plus a `Progress` test that drains the queue and asserts it empties, and a
`test_cancel_returns_ticket_to_stock` that checks a refund restores stock.
The spec tells us *what* to assert; the fuzzer drives the *real* code.

### 2. Behavior: the state-space mirror (the strongest check)

`tests/test_state_space_mirror.py` performs a breadth-first search over the
concrete code — driving real `request()`/`serve()`/`cancel()` calls — and
asserts the reachable state space is **isomorphic to the TLA+ model**:

- every reachable state satisfies the invariants, and
- the number of distinct states equals what TLC reported: **75**.

```
concrete code explores 75 distinct states  ==  TLC explores 75  ✔
```

If the code ever gains an extra transition, drops a guard, or reaches a state
the spec can't, the count (or an invariant) diverges and the test fails. This
is as close as you get to "the code is proven to match the spec" without
writing the system in a verification language.

### 3. Structure: the pydeps graph, observed and accepted by merging

Structure is *observed*, and *accepted by merging*. `code/observe.py` runs
pydeps over `code/reservation/` to get the live dependency graph. Two distinct
modes:

- **Observation** — diff the live graph against a reference: the committed
  baseline, a target branch (`--against main`), or a PR's base branch
  (`--pr N`). This is the "what did this branch change structurally?" view.
  It never blocks.
- **Acceptance gate** — `--check` fails if the committed baseline is out of
  sync with the code. The pre-commit hook (`.githooks/pre-commit`) regenerates
  the baseline on commit; CI enforces `--check` for everyone. **Merging is the
  act that accepts a structural change** — the baseline is the record of the
  accepted state.

```
$ python3 code/observe.py --against main
### Architecture observation (vs main)
_Observation only — not a gate. Merging accepts the change._
**New modules**
- `cancellation`
**New dependencies**
- `cancellation -> inventory`
- `cancellation -> ledger`
- `system -> cancellation`
```

`tests/test_architecture.py` is the lightweight CI companion: it asserts the
module graph is a DAG (no import cycles), that the system wires all its
modules, and that the committed baseline is in sync with the live graph. The
last check is the acceptance-loop hygiene rule — it doesn't forbid the code
from changing, it just makes sure the baseline (the accepted state) is
current. If the code moved, the test points you at `observe.py --save-baseline`.

## Running it all

```sh
cd code
python3 -m pip install -r requirements.txt
python3 -m pytest -q          # 13 tests: invariants, state-space mirror, architecture

python3 observe.py            # diff the live graph vs the baseline
python3 observe.py --against main   # diff vs a target branch (a PR's delta)
python3 observe.py --pr 4     # post that delta as a PR comment
python3 observe.py --check    # gate: fail if the baseline is out of sync
python3 observe.py --save-baseline   # regenerate the baseline (accept the state)
```

## Bottom line

| Spec | Code | Bridge (in CI) |
|------|------|----------------|
| TLA+ invariants | Python impl | property-based tests (Hypothesis) |
| TLA+ state space (75 states) | Python impl | BFS state-space mirror test |
| module structure | Python imports | pydeps graph vs committed baseline (`observe.py`) |

The spec and the code now *check each other* — behavior via the invariants and
state space (control: the spec is proven), structure via the pydeps graph and
baseline (observation: the structure is revealed, advertised against the target
branch, and accepted by merging). That is the practical answer to "how do I
know the spec still mirrors the code?" — for behavior you **prove** it; for
structure you **observe** it and **accept it by merging**.
