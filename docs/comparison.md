# TLA+ vs pydeps — Distinction and Complementarity

This is the core of the RJR-267 proof of concept. Both tools describe the
*same* reservation counter, but they answer **different questions** and
**neither can do the other's job**.

## The one-line distinction

> **TLA+ specifies *behavior* and proves *correctness*.**
> **pydeps reveals *structure* and shows *change*.**

- TLA+ is a **formal method**: a mathematical model of what the system *does*,
  checked exhaustively by a model checker.
- pydeps is a **dependency analyzer**: it reads the code's imports and renders
  the module dependency graph — a picture of what the system *is made of*,
  derived from the code rather than declared about it.

## Side-by-side

| Dimension | TLA+ | pydeps |
|-----------|------|--------|
| **Question answered** | "Is the behavior correct?" | "What does the code depend on, and how is it changing?" |
| **Abstraction level** | State & transitions (below code) | Modules & imports (at the code level) |
| **Primary artifact** | A formal spec + a proof/counterexample | A dependency graph (JSON/SVG/PNG) + a diff |
| **Verification** | Exhaustive model checking (TLC) — *mathematical* | None — it *reveals*, it doesn't *prove* |
| **Source of truth** | The spec (authored) | The code (derived) |
| **Finds bugs?** | Yes — counterexample traces | No — it can't express "never oversell" |
| **Shows structure?** | Poorly — state variables, not modules | Yes — the whole point |
| **Shows change?** | Not really | Yes — diff the graph against a baseline |
| **Audience** | Engineers/verifiers | Engineers, architects, reviewers |
| **Output format** | Text (states, traces) | Graph (SVG/PNG) + JSON + text diff |

## What each one *cannot* do

This is the cleanest way to see the distinction:

**pydeps cannot express or check the reservation rules.** You cannot write
"never sell more tickets than stock" as a dependency edge. Its
`serving -> inventory` edge is a *fact about imports*, not a *rule*. It tells
you the Serving Logic module *imports* Inventory; it says nothing about whether
that interaction is correct.

**TLA+ cannot show you the architecture.** The spec has `inventory`,
`pending`, `sold`, `rejected` — *state variables*, not modules. It has no
notion of "intake" vs "serving" as importable units, no dependency graph, no
diagram. If you asked a reviewer "what does this codebase look like?", a TLA+
spec is not the answer.

## How they complement each other

They sit at **different rungs of the abstraction ladder** and lock together:

```
        ┌─────────────────────────────────────────────┐
        │  pydeps:  WHAT the code is made of           │  ← structure
        │  (modules, imports, and how it's changing)   │     (observed)
        └──────────────────────┬──────────────────────┘
                               │  each module has *behavior*
                               │  that must be right
        ┌──────────────────────▼──────────────────────┐
        │  TLA+:  HOW the behavior must be correct     │  ← behavior
        │  (state, transitions, invariants, liveness)  │     (proven)
        └─────────────────────────────────────────────┘
```

1. **pydeps gives the skeleton; TLA+ fills in the correctness.**
   The dependency graph tells you *where* the serving logic lives and *what it
   imports*. The TLA+ spec pins down *what that logic is allowed to do* and
   proves it never oversells.

2. **The TLA+ state maps onto the pydeps modules.**
   `inventory` → the **inventory** module; `sold`/`rejected` → the **ledger**
   module; `pending` + `Serve` → the **serving** module; `Request` → the
   **intake** module. The formal model and the dependency graph are two
   projections of the same reality.

3. **They catch different classes of mistake.**
   - A *structural* mistake (a new module, an inverted dependency, a cycle)
     shows up as a delta in the pydeps graph — and `observe.py` advertises it.
   - A *behavioral* mistake (oversell, starvation, deadlock) is invisible in
     the graph but caught by TLC — exactly as it caught the two bugs in
     [tla-plus.md](tla-plus.md#bugs-tlc-caught-during-development).

4. **They're both "as-code" and both verifiable in CI.**
   The TLA+ spec is checked by TLC; the pydeps graph is derived from the code
   and diffed against a baseline by `observe.py`. Together they give a repo
   that is *both* provably-correct *and* self-documenting about its own
   structure.

## A concrete trace of the complementarity

Take the property **"never oversell"**:

- In **pydeps** it appears only as the edge `serving -> inventory` — a *fact*
  that the serving module imports inventory.
- In **TLA+** it is the invariant `NoOversell == inventory >= 0` and
  `BoundedSales == soldCount <= MaxInventory` — *proven* to hold over all 29
  reachable states.

The graph says *that* the serving logic touches inventory; the model check says
*how* it may touch it and that the result is always safe. One without the other
is incomplete: the graph alone can't be trusted, the proof alone can't be
understood by the team.

## Why pydeps instead of a hand-written architecture model?

The architecture half originally used Structurizr (a hand-written C4 model).
It was dropped for pydeps because the goal shifted from *defining* the
architecture to *observing* it:

- A hand-written model **drifts** — you must remember to update it when the
  code changes, and it silently lies when you don't.
- A pydeps graph is **derived** — it can't drift from the code, because it
  *is* the code's imports. The only thing that can be stale is the *baseline*
  (the last observed state), and that's a one-command update.
- For a project being **bootstrapped**, you want to *see* the structure
  evolve, not *constrain* it. pydeps + a baseline is observation; a
  hand-written model is control. Observation is the right mode here.

## Bottom line

- Use **pydeps** to *see* the architecture and *watch it change*.
- Use **TLA+** to *prove* the behavior is correct.
- Use **both** to get a system that is simultaneously *understandable* and
  *verified* — the distinction is the feature, not a gap.
