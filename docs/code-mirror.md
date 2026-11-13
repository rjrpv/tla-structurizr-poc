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
│   ├── system.py                # ReservationSystem — wires the 4 modules
│   ├── intake.py                # RequestIntake  (owns `pending`)
│   ├── serving.py               # ServingLogic   (the sell/reject decision)
│   ├── inventory.py             # Inventory      (owns `inventory`)
│   └── ledger.py                # Ledger         (owns `sold`/`rejected`/`soldCount`)
├── tests/
│   ├── test_invariants.py       # property-based: TLA+ invariants on the code
│   ├── test_state_space_mirror.py  # BFS the code; assert 29 states == TLC
│   └── test_architecture.py     # well-formedness: no cycles + baseline in sync
├── observe.py                   # pydeps-based architecture observer
├── baseline.json                # the committed dependency graph (last observed)
└── requirements.txt
```

## The bridges

### 1. Behavior: TLA+ invariants → property-based tests

The TLA+ spec declares `NoOversell`, `BoundedSales`, and `Progress`.
`tests/test_invariants.py` runs the *concrete* Python code with randomized
request/serve interleavings (Hypothesis) and asserts the **same invariants hold
after every step**:

```python
assert sys.inventory.stock >= 0          # NoOversell
assert sys.ledger.sold_count <= sys.max_inventory  # BoundedSales
```

plus a `Progress` test that drains the queue and asserts it empties. The spec
tells us *what* to assert; the fuzzer drives the *real* code.

### 2. Behavior: the state-space mirror (the strongest check)

`tests/test_state_space_mirror.py` performs a breadth-first search over the
concrete code — driving real `request()`/`serve()` calls — and asserts the
reachable state space is **isomorphic to the TLA+ model**:

- every reachable state satisfies the invariants, and
- the number of distinct states equals what TLC reported: **29**.

```
concrete code explores 29 distinct states  ==  TLC explores 29  ✔
```

If the code ever gains an extra transition, drops a guard, or reaches a state
the spec can't, the count (or an invariant) diverges and the test fails. This
is as close as you get to "the code is proven to match the spec" without
writing the system in a verification language.

### 3. Structure: the pydeps graph, observed against a baseline

Structure is *observed*, not enforced. `code/observe.py` runs pydeps over
`code/reservation/` to get the live dependency graph, then diffs it against
`code/baseline.json` — the graph as of the last time we looked.

```
$ python3 code/observe.py
### Architecture observation
_Observation only — not a gate._
**New modules**
- `notifications`
**New dependencies**
- `serving -> notifications`
_To accept this as the new baseline: `python3 code/observe.py --save-baseline`_
```

The baseline is a plain JSON file you own; the diff between it and the live
graph is the unit of observation. When the code changes, you *see* it and
decide: accept it (`--save-baseline`) or fix the code (and the observation
converges back). Nothing blocks the build — for a project being bootstrapped,
the goal is to course-correct, not to define boundary conditions.

`tests/test_architecture.py` is the lightweight CI companion: it asserts the
module graph is a DAG (no import cycles), that the system wires all four
modules, and that the committed baseline is in sync with the live graph. The
last check is the observation-mode hygiene rule — it doesn't forbid the code
from changing, it just makes sure the baseline (what we last observed) is
current. If the code moved, the test points you at `observe.py --save-baseline`.

## Running it all

```sh
cd code
python3 -m pip install -r requirements.txt
python3 -m pytest -q          # 11 tests: invariants, state-space mirror, well-formedness

python3 observe.py            # diff the live graph vs the baseline
python3 observe.py --pr 2     # post the observation as a PR comment
python3 observe.py --save-baseline   # accept the current state as the baseline
```

## Bottom line

| Spec | Code | Bridge (in CI) |
|------|------|----------------|
| TLA+ invariants | Python impl | property-based tests (Hypothesis) |
| TLA+ state space (29 states) | Python impl | BFS state-space mirror test |
| module structure | Python imports | pydeps graph vs committed baseline (`observe.py`) |

The spec and the code now *check each other* — behavior via the invariants and
state space (control: the spec is proven), structure via the pydeps graph and
baseline (observation: the structure is revealed and watched). That is the
practical answer to "how do I know the spec still mirrors the code?" — for
behavior you **prove** it; for structure you **observe** it.
