# RJR-267 — TLA+ and Structurizr Proof of Concept

A small, self-contained proof of concept that models **one system** — a
ticket-reservation counter — in two complementary ways:

| Half | Tool | Question it answers | Verifies |
|------|------|---------------------|----------|
| **Behavior** | [TLA+](https://lamport.azurewebsites.net/tla/) + TLC | *What can the system do, and is it always correct?* | Correctness (exhaustive model checking) |
| **Architecture** | [Structurizr](https://structurizr.com/) | *What are the parts, and how do they relate?* | Structure (architecture-as-code, diagrams) |

The point of the PoC is the **distinction and the complementarity**: the same
system, described at two different levels of abstraction, each tool doing what
the other cannot. A **Python reference implementation** plus a test suite then
close the loop by checking the code against both specs — see
[docs/code-mirror.md](docs/code-mirror.md).

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
├── structurizr/
│   ├── reservation.dsl           # the intended architecture (Structurizr DSL)
│   ├── generated_from_code.dsl   # the actual architecture (derived from code/)
│   └── diagrams/
│       ├── index.html            # interactive static site (open in a browser)
│       ├── context.png           # system context view
│       ├── container.png         # container view
│       └── dynamic.png           # dynamic (request → serve) view
├── code/
│   ├── reservation/              # Python reference implementation (4 containers)
│   ├── tests/                    # invariants, state-space mirror, architecture
│   ├── generate_dsl.py           # code -> Structurizr DSL (the "flip")
│   └── requirements.txt
└── docs/
    ├── tla-plus.md               # the behavioral half, explained
    ├── structurizr.md            # the architectural half, explained
    ├── comparison.md             # the distinction + complementarity (the crux)
    └── code-mirror.md            # how the code is checked against both specs
```

## Quick start

### TLA+ (behavior)

```sh
java -cp ~/tools/tla2tools-174.jar tlc2.TLC tla/ReservationSystem
```

Expected: `Model checking completed. No error has been found.`
(`NoOversell` and `BoundedSales` invariants hold; `Progress` liveness holds.)

### Structurizr (architecture)

```sh
# validate
structurizr validate -w structurizr/reservation.dsl
# export the static site
structurizr export -w structurizr/reservation.dsl -f static -o structurizr/diagrams
# then open structurizr/diagrams/index.html in a browser
```

### Code (the mirror)

```sh
cd code
python3 -m pip install -r requirements.txt
python3 -m pytest -q          # 13 tests: invariants, state-space mirror, architecture
python3 generate_dsl.py       # regenerate the model from the code
```

## The result

- **TLA+**: TLC explored **29 distinct states** (84 generated) and confirmed all
  three properties hold. During development it also caught two real modeling
  bugs (an underspecified action and a terminal-state deadlock) — see
  [docs/tla-plus.md](docs/tla-plus.md).
- **Structurizr**: the same system rendered as three diagrams — context,
  container, and dynamic — generated from a single declarative model.
- **Code**: a Python reference implementation passes **13 tests** that check it
  against both specs — the TLA+ invariants (property-based), a state-space
  mirror (the code explores the same **29** states TLC found), and the
  Structurizr edges (import-graph architecture test). Regenerating the model
  from the code (`generate_dsl.py`) reproduces the intended architecture
  exactly (drift check passes).

Read [docs/comparison.md](docs/comparison.md) for the core argument: why these
two tools are **different, not competing**, and how they reinforce each other.
See [docs/code-mirror.md](docs/code-mirror.md) for how the code is checked
against both specs.
