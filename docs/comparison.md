# TLA+ vs Structurizr — Distinction and Complementarity

This is the core of the RJR-267 proof of concept. Both tools describe the
*same* reservation counter, but they answer **different questions** and
**neither can do the other's job**.

## The one-line distinction

> **TLA+ specifies *behavior* and proves *correctness*.**
> **Structurizr specifies *structure* and produces *diagrams*.**

- TLA+ is a **formal method**: a mathematical model of what the system *does*,
  checked exhaustively by a model checker.
- Structurizr is an **architecture-as-code** tool: a declarative model of what
  the system *is made of*, rendered as diagrams.

## Side-by-side

| Dimension | TLA+ | Structurizr |
|-----------|------|-------------|
| **Question answered** | "Is the behavior correct?" | "What is the architecture?" |
| **Abstraction level** | State & transitions (below code) | Systems, containers, components (above code) |
| **Primary artifact** | A formal spec + a proof/counterexample | A model + generated diagrams |
| **Verification** | Exhaustive model checking (TLC) — *mathematical* | None — it *describes*, it doesn't *prove* |
| **What it guarantees** | Properties hold over **all** reachable behaviors | Diagrams always match the model (no drift) |
| **Finds bugs?** | Yes — counterexample traces | No — it can't express "never oversell" |
| **Shows structure?** | Poorly — state variables, not components | Yes — the whole point |
| **Audience** | Engineers/verifiers | Engineers, architects, product, stakeholders |
| **Output format** | Text (states, traces) | Images (SVG/PNG) + interactive site |
| **Scale of truth** | Every interleaving (within model bounds) | The declared topology |

## What each one *cannot* do

This is the cleanest way to see the distinction:

**Structurizr cannot express or check the reservation rules.** You cannot write
"never sell more tickets than stock" in the DSL — there's no notion of state,
transition, or temporal property. Its `serving -> inventory "reads /
decrements stock"` edge is a *label*, not a *rule*. It tells you the Serving
Logic *talks to* Inventory; it says nothing about whether that interaction is
correct.

**TLA+ cannot show you the architecture.** The spec has `inventory`,
`pending`, `sold`, `rejected` — *state variables*, not components. It has no
notion of "Request Intake" vs "Serving Logic" as deployable units, no
"HTTP" protocol, no diagram. If you asked a stakeholder "what does this
system look like?", a TLA+ spec is not the answer.

## How they complement each other

They sit at **different rungs of the abstraction ladder** and lock together:

```
        ┌─────────────────────────────────────────────┐
        │  Structurizr:  WHAT the system is made of    │  ← structure
        │  (systems, containers, components, edges)    │     (diagrams)
        └──────────────────────┬──────────────────────┘
                               │  each edge / container
                               │  has *behavior* that must be right
        ┌──────────────────────▼──────────────────────┐
        │  TLA+:  HOW the behavior must be correct     │  ← behavior
        │  (state, transitions, invariants, liveness)  │     (proof)
        └─────────────────────────────────────────────┘
```

1. **Structurizr gives the skeleton; TLA+ fills in the correctness.**
   The container view tells you *where* the serving logic lives and *what it
   talks to*. The TLA+ spec pins down *what that logic is allowed to do* and
   proves it never oversells.

2. **The TLA+ state maps onto the Structurizr containers.**
   `inventory` → the **Inventory** container; `sold`/`rejected` → the
   **Ledger** container; `pending` + `Serve` → the **Serving Logic**
   container; `Request` → the **Request Intake** container. The formal model
   and the architectural model are two projections of the same reality.

3. **They catch different classes of mistake.**
   - A *structural* mistake (wrong component, missing edge, bad dependency)
     is visible in the Structurizr diagrams.
   - A *behavioral* mistake (oversell, starvation, deadlock) is invisible in
     the diagrams but caught by TLC — exactly as it caught the two bugs in
     [tla-plus.md](tla-plus.md#bugs-tlc-caught-during-development).

4. **They're both "as-code" and both verifiable in CI.**
   The TLA+ spec is checked by TLC; the Structurizr model is validated by
   `structurizr validate` and its diagrams are generated, never hand-drawn.
   Together they give a repo that is *both* provably-correct *and*
   self-documenting.

## A concrete trace of the complementarity

Take the property **"never oversell"**:

- In **Structurizr** it appears only as the edge
  `serving -> inventory "reads / decrements stock"` — a *declaration* that the
  interaction exists.
- In **TLA+** it is the invariant `NoOversell == inventory >= 0` and
  `BoundedSales == soldCount <= MaxInventory` — *proven* to hold over all 29
  reachable states.

The diagram says *that* the serving logic touches inventory; the model check
says *how* it may touch it and that the result is always safe. One without the
other is incomplete: the diagram alone can't be trusted, the proof alone
can't be understood by the team.

## Bottom line

- Use **Structurizr** to *communicate* the architecture and keep it in sync.
- Use **TLA+** to *prove* the behavior is correct.
- Use **both** to get a system that is simultaneously *understandable* and
  *verified* — the distinction is the feature, not a gap.
