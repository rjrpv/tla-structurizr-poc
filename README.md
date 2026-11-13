# RJR-267 — TLA+ and pydeps Proof of Concept

A small, self-contained proof of concept that models **one system** — a
ticket-reservation counter — in two complementary ways:

| Half | Tool | Question it answers | Verifies |
|------|------|---------------------|----------|
| **Behavior** | [TLA+](https://lamport.azurewebsites.net/tla/) + TLC | *What can the system do, and is it always correct?* | Correctness (exhaustive model checking) |
| **Architecture** | [pydeps](https://github.com/pydeps/pydeps) | *What does the code depend on, and how is it changing?* | Structure (dependency graph, observed over time) |

The point of the PoC is the **distinction and the complementarity**: the same
system, described at two different levels of abstraction, each tool doing what
the other cannot. A **Python reference implementation** plus a test suite then
close the loop by checking the code against the spec — see
[docs/code-mirror.md](docs/code-mirror.md).

> **Note on tooling.** The architecture half originally used Structurizr
> (hand-written C4 model). It was dropped in favor of **pydeps** because the
> goal shifted from *defining* the architecture to *observing* it: pydeps
> derives the graph from the code directly, so there is no hand-maintained
> model to drift out of sync. See [docs/comparison.md](docs/comparison.md).

## The system (in one sentence)

A counter keeps a stock of `MaxInventory` tickets; a finite set of customers
each request at most once; a pending request is served — sold if stock remains,
rejected otherwise. The interesting property: **it must never oversell, and
every request must eventually be answered.**

## Layout

```
.
├── tla/
│   ├── ReservationSystem.tla     # the behavioral model (TLA+)
│   ├── ReservationSystem.cfg     # TLC model: 2 tickets, 3 customers
│   └── tlc_output.txt            # captured TLC run (all properties pass)
├── code/
│   ├── reservation/              # Python reference implementation (4 modules)
│   │   ├── system.py             #   wires the four modules
│   │   ├── intake.py             #   RequestIntake  (owns `pending`)
│   │   ├── serving.py            #   ServingLogic   (sell/reject decision)
│   │   ├── inventory.py          #   Inventory      (owns `inventory`)
│   │   └── ledger.py             #   Ledger         (owns `sold`/`rejected`)
│   ├── tests/                    # invariants, state-space mirror, well-formedness
│   ├── observe.py                # pydeps-based architecture observer
│   ├── baseline.json             # the committed dependency graph (last observed)
│   └── requirements.txt
└── docs/
    ├── tla-plus.md               # the behavioral half, explained
    ├── comparison.md             # the distinction + complementarity (the crux)
    ├── code-mirror.md            # how the code is checked against the spec
    └── delta-diagram.html        # the code->graph delta, advertised in the PR
```

## Quick start

### TLA+ (behavior)

```sh
java -cp ~/tools/tla2tools-174.jar tlc2.TLC tla/ReservationSystem
```

Expected: `Model checking completed. No error has been found.`
(`NoOversell` and `BoundedSales` invariants hold; `Progress` liveness holds.)

### Code (the mirror)

```sh
cd code
python3 -m pip install -r requirements.txt
python3 -m pytest -q          # 11 tests: invariants, state-space mirror, well-formedness
```

### Architecture (observe, don't gate)

```sh
python3 code/observe.py                    # diff the live graph vs baseline
python3 code/observe.py --pr 2             # post the observation as a PR comment
python3 code/observe.py --save-baseline    # accept the current state as the baseline
```

## The result

- **TLA+**: TLC explored **29 distinct states** (84 generated) and confirmed all
  three properties hold. During development it also caught two real modeling
  bugs (an underspecified action and a terminal-state deadlock) — see
  [docs/tla-plus.md](docs/tla-plus.md).
- **Code**: a Python reference implementation passes **11 tests** that check it
  against the spec — the TLA+ invariants (property-based), a state-space mirror
  (the code explores the same **29** states TLC found), and architecture
  well-formedness (no import cycles; the committed baseline is in sync).
- **Architecture**: `observe.py` runs pydeps over the code and diffs the graph
  against `baseline.json`. It *observes* drift and advertises it in the PR — it
  does not block the build. That's the right mode for a project being
  bootstrapped: course-correct, don't control.

Read [docs/comparison.md](docs/comparison.md) for the core argument: why TLA+
and pydeps are **different, not competing**, and how they reinforce each other.
See [docs/code-mirror.md](docs/code-mirror.md) for how the code is checked
against the spec, and [docs/delta-diagram.html](docs/delta-diagram.html) for
what the observed delta looks like in a PR.
