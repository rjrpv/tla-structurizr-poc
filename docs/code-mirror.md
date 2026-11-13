# Making the Specs Mirror the Code

This is the follow-up to [comparison.md](comparison.md). The PoC showed TLA+ and
Structurizr describing the *same* system at two abstractions. This document
closes the loop: it adds a **Python reference implementation** and a set of
**tests that check the code against both specs**, so the "mirror" is enforced
by the build rather than by convention.

The guiding idea: **the spec is the source of truth; the code is a candidate
implementation; the tests are the bridge that proves the candidate matches.**

## What was added

```
code/
├── reservation/                 # the reference implementation
│   ├── system.py                # ReservationSystem — wires the 4 containers
│   ├── intake.py                # RequestIntake  (owns `pending`)
│   ├── serving.py               # ServingLogic   (the sell/reject decision)
│   ├── inventory.py             # Inventory      (owns `inventory`)
│   └── ledger.py                # Ledger         (owns `sold`/`rejected`/`soldCount`)
├── tests/
│   ├── test_invariants.py       # property-based: TLA+ invariants on the code
│   ├── test_state_space_mirror.py  # BFS the code; assert 29 states == TLC
│   └── test_architecture.py     # import graph == Structurizr edges
├── generate_dsl.py              # code -> Structurizr DSL (the "flip")
└── requirements.txt
structurizr/
└── generated_from_code.dsl      # the model DERIVED from the code
```

## The three bridges

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

### 3. Structure: Structurizr edges → architecture tests

`tests/test_architecture.py` is the Python equivalent of an ArchUnit/NDepend
rule. It statically reads the imports in `code/reservation/` and asserts the
dependency direction matches `structurizr/reservation.dsl`:

```
intake    -> serving      (RequestIntake drives ServingLogic)
serving   -> inventory    (ServingLogic reads/decrements Inventory)
serving   -> ledger       (ServingLogic records in the Ledger)
```

plus: data containers (`inventory`, `ledger`) are dependency-free, and the
graph is a DAG (no cycles). A structural mistake — an inverted dependency, a
new cycle — fails the build.

## The flip: generating the model from the code

`code/generate_dsl.py` statically analyzes `code/reservation/` (classes →
containers, `from .X import` → edges) and emits
`structurizr/generated_from_code.dsl` — a model **derived from the code**, not
hand-written. Because it's derived, it can't drift: change the imports, re-run,
and the model changes with them.

Running it and validating:

```
$ python3 code/generate_dsl.py
  containers: Request Intake, Inventory, Ledger, Serving Logic
  relationships: 3

$ structurizr validate -w structurizr/generated_from_code.dsl
  (valid)
```

The generated model:

```
intake -> serving
serving -> inventory
serving -> ledger
```

## The drift check: intended vs actual

Now we have two models of the *same* system:

- **intended** — `structurizr/reservation.dsl` (hand-written, the design)
- **actual** — `structurizr/generated_from_code.dsl` (derived from the code)

Diffing their container sets and edges:

```
intended:  intake->serving, serving->inventory, serving->ledger
actual:    intake->serving, serving->inventory, serving->ledger
DRIFT CHECK: PASS — code-derived model matches the intended model exactly.
```

This is the structural analogue of the state-space mirror: the *actual*
architecture (from code) matches the *intended* architecture (the design).

## A note on the bundled CLI

The `structurizr-cli` `inspect` command is for **workspace validation** (model
quality checks), not source-code analysis, and the bundled `structurizr-import`
jar ships only documentation/diagram importers — no Python code analyzer. So
the "flip" here is a small purpose-built generator (`generate_dsl.py`) rather
than a one-shot CLI import. For larger codebases the same idea maps onto
dedicated tools: Structurizr's code import (Java/C#/JS/TS/Go), or
`dependency-cruiser`/`jdeps`/`pydeps` for the dependency graph.

## Running it all

```sh
cd code
python3 -m pip install -r requirements.txt
python3 -m pytest -q          # 13 tests: invariants, state-space mirror, architecture

python3 generate_dsl.py       # regenerate the model from the code
# then validate: structurizr validate -w ../structurizr/generated_from_code.dsl
```

## Bottom line

| Spec | Code | Bridge (in CI) |
|------|------|----------------|
| TLA+ invariants | Python impl | property-based tests (Hypothesis) |
| TLA+ state space (29 states) | Python impl | BFS state-space mirror test |
| Structurizr edges | Python imports | architecture test (import graph) |
| intended model | actual model | code→DSL generation + diff |

The specs and the code now *check each other* in both directions — behavior
via the invariants and state space, structure via the import graph and the
generated-model diff. That is the practical answer to "how do I know the spec
still mirrors the code?" — you don't trust it, you **test it**.
