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
├── examples/                     # canonical TLA+ scenarios (RJR-275)
│   ├── README.md                 #   what each is, and how to run them
│   ├── TrafficLight.tla ...      #   8 one-property models (leader election,
│   ├── *.cfg                     #   inventory, consensus, ...)
│   ├── code/                     #   Python mirror of each model
│   ├── tests/                    #   state-space mirror test (the anchor)
│   └── tlc_output.txt            #   captured TLC runs (all pass)
├── code/
│   ├── reservation/              # Python reference implementation (6 modules)
│   │   ├── system.py             #   wires the modules
│   │   ├── intake.py             #   RequestIntake  (owns `pending`)
│   │   ├── serving.py            #   ServingLogic   (sell/reject decision)
│   │   ├── inventory.py          #   Inventory      (owns `inventory`)
│   │   ├── ledger.py             #   Ledger         (owns `sold`/`rejected`/`canceled`)
│   │   └── cancellation.py       #   Cancellation   (cancel/refund; restocks)
│   ├── tests/                    # invariants, state-space mirror, architecture
│   ├── observe.py                # pydeps observer + acceptance gate
│   ├── baseline.json             # the committed dependency graph (the accepted state)
│   └── requirements.txt
├── .githooks/pre-commit          # keeps baseline.json in sync on commit
├── .github/workflows/ci.yml      # tests + baseline gate + TLC on every PR
├── Makefile                      # make install-hooks / check / test / observe / tla
├── AGENTS.md                     # workflow rules for agents (and humans)
├── .agents/skills/               # the tla-plus-workflow skill
└── docs/
    ├── tla-plus.md               # the behavioral half, explained
    ├── comparison.md             # the distinction + complementarity (the crux)
    └── code-mirror.md            # how the code is checked against the spec
```

## Quick start

### TLA+ (behavior)

```sh
java -jar tla2tools.jar -workers auto tla/ReservationSystem
```

Expected: `Model checking completed. No error has been found.`
(`NoOversell` and `BoundedStock` invariants hold; `Progress` liveness holds.)

### Canonical examples (RJR-275)

Eight very simple, one-property TLA+ models of canonical scenarios — leader
election, inventory checking, consensus, and more:

```sh
make examples                          # model-check all eight
java -jar tla2tools.jar -workers auto examples/LeaderElection   # or one
make examples-py                       # the Python mirror: state space == TLC
```

See [examples/README.md](examples/README.md) for what each is about, and how
the Python mirror anchors the tests to the models and their state spaces.

### Code (the mirror)

```sh
cd code
python3 -m pip install -r requirements.txt
python3 -m pytest -q          # 13 tests: invariants, state-space mirror, architecture
```

### Architecture (observe, then accept by merging)

```sh
python3 code/observe.py                    # diff the live graph vs the baseline
python3 code/observe.py --against main     # diff vs a target branch (a PR's delta)
python3 code/observe.py --pr 4             # post that delta as a PR comment
python3 code/observe.py --check            # gate: fail if baseline is out of sync
python3 code/observe.py --save-baseline    # regenerate the baseline (accept the state)
```

Install the pre-commit hook once per clone so the baseline stays in sync:

```sh
make install-hooks          # = git config core.hooksPath .githooks
```

(The `Makefile` also wraps the other steps: `make check`, `make test`,
`make observe`, `make tla`.)

## The result

- **TLA+**: TLC explored **75 distinct states** and confirmed all three
  properties hold. During development it also caught real modeling bugs —
  including a counterexample showing the old `soldCount` bound was wrong once
  tickets could be refunded — see [docs/tla-plus.md](docs/tla-plus.md).
- **Code**: a Python reference implementation passes **13 tests** that check it
  against the spec — the TLA+ invariants (property-based), a state-space mirror
  (the code explores the same **75** states TLC found), and architecture
  well-formedness (no import cycles; the committed baseline is in sync).
- **Architecture**: `observe.py` runs pydeps over the code. It *observes* the
  structural delta (advertised in the PR, against the target branch) and *gates*
  on the baseline staying in sync with the code (`--check`). **Merging a PR is
  the act that accepts a structural change** — the baseline is the record of
  the accepted state. That's the right mode for a project being bootstrapped:
  course-correct and keep the record honest, don't gate on opinion.

## The acceptance loop

1. **Logic** lives in the TLA+ spec; TLC must pass and any finding is noted in
   the PR.
2. **Code** mirrors the spec; the state-space mirror test proves the code
   explores the same states TLC does.
3. **Structure** is observed with pydeps; the delta is advertised against the
   target branch.
4. **Acceptance** = merging: the pre-commit hook keeps `baseline.json` in sync
   and CI's `--check` gate blocks a merge if it isn't.

The full rules for agents (and humans) are in [AGENTS.md](AGENTS.md) and
`.agents/skills/tla-plus-workflow/SKILL.md`.

Read [docs/comparison.md](docs/comparison.md) for the core argument: why TLA+
and pydeps are **different, not competing**, and how they reinforce each other.
See [docs/code-mirror.md](docs/code-mirror.md) for how the code is checked
against the spec.
