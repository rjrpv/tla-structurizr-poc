# AGENTS.md — RJR-267

This repo pairs a TLA+ spec (`tla/ReservationSystem.tla`) with a Python
reference implementation (`code/reservation/`) that mirrors it. The workflow is
**observe-not-gate**: the spec is the source of truth for behavior, the code is
checked against it, and structural changes are *advertised* and accepted by
merging (not gated on opinion).

**Full workflow rules: see `.agents/skills/tla-plus-workflow/SKILL.md`.** The
short version:

1. **Logic changes go in TLA+ first.** Edit the spec, run TLC
   (`java -jar tla2tools.jar -workers auto tla/ReservationSystem`), update
   `tla/tlc_output.txt`. A TLC counterexample is a *finding* about the model —
   fix the model, then re-run.
2. **Tests mirror the spec.** Update `code/tests/` in the same change. The
   state-space mirror test must expect the **same distinct-state count as TLC**.
   `cd code && python3 -m pytest -q` must be green.
3. **Note the TLA+ delta + findings in the PR** — the modeling decision, any
   counterexample (show the trace), and the state count before → after.
4. **Advertise the structural delta against the target branch**:
   `python3 code/observe.py --against <base>` or `--pr <N>`. Put the graph in
   the PR. The pre-commit hook (`.githooks/pre-commit`) keeps
   `code/baseline.json` in sync; CI (`code/observe.py --check`) blocks a merge
   if the baseline is stale. **Merging is the acceptance.**

## Commands

| Task | Command |
|---|---|
| Model-check the spec | `java -jar tla2tools.jar -workers auto tla/ReservationSystem` |
| Run tests | `cd code && python3 -m pytest -q` |
| Baseline gate (must pass to merge) | `python3 code/observe.py --check` |
| Structure delta vs a branch | `python3 code/observe.py --against main` |
| Post structure delta on a PR | `python3 code/observe.py --pr <N>` |
| Accept the current structure | `python3 code/observe.py --save-baseline` |
| Install the pre-commit hook | `git config core.hooksPath .githooks` |

## Invariants (spec)

- `NoOversell` — `inventory >= 0`
- `BoundedStock` — `inventory <= MaxInventory`
- `Progress` — `[]<>(pending = {})`
