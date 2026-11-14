---
name: tla-plus-workflow
description: How to make changes to this repo (RJR-267). Use whenever touching the TLA+ spec, the Python reference implementation, tests, or the code structure, or when opening a PR. Enforces the observe-not-gate acceptance loop: TLA+ for logic, tests mirroring the spec, and the structural delta advertised against the target branch.
---

# TLA+ / observe-not-gate workflow

This repo pairs a TLA+ spec (`tla/ReservationSystem.tla`) with a Python
reference implementation (`code/reservation/`) that mirrors it. The point of
the project is **intellectual control**: the spec is the source of truth for
behavior, the code is checked against it, and structural changes are
*advertised* (and accepted by merging) rather than gated on opinion.

Follow these rules for any change.

## 1. Logic changes go in TLA+ first

- Any change to *behavior* (a new action, a new state, a new invariant) starts
  as a change to `tla/ReservationSystem.tla`. Do not invent behavior in the
  Python code and back-port it.
- Run TLC after editing the spec:
  ```
  java -jar tla2tools.jar tlc2.TLC tla/ReservationSystem
  ```
  (the jar is in `~/tools/` locally; CI downloads it). All invariants must
  hold and `tla/tlc_output.txt` must be updated to the fresh result.
- If TLC finds a counterexample, **that is the finding** — it usually means the
  model (an invariant or a variable) is wrong, not that the code is wrong. Fix
  the model, then re-run.

## 2. Tests must stay consistent with TLA+

- The Python tests mirror the spec. When the spec changes, update the tests in
  the same change:
  - `code/tests/test_invariants.py` — the invariants, in code.
  - `code/tests/test_state_space_mirror.py` — the concrete code must explore
    **exactly the same number of distinct states** as TLC reports. If TLC says
    75, the mirror test expects 75. This is the tie-back that proves the code
    still mirrors the spec.
- Run the suite: `cd code && python3 -m pytest -q`. All tests must pass.

## 3. Note the TLA+ delta and findings in the PR

The PR body must explain the *modeling decision*, not just list files. Include:
- What changed in the spec (new action/state/invariant, what was removed).
- Any TLC finding — especially a counterexample — and what it told you. A
  counterexample is the strongest explanation of *why* the model changed; show
  the trace (a small table of the key states) rather than burying it.
- The TLC state count before → after, and confirmation that invariants hold.
- A short "how to read this" for the reviewer (behavior vs structure vs tests).

## 4. Advertise structural changes against the target branch

The code's dependency graph is observed with `code/observe.py`. For a PR:
- Diff the structure **against the PR's base branch**, not the old baseline:
  ```
  python3 code/observe.py --against <base-branch>     # e.g. --against main
  python3 code/observe.py --pr <N>                    # auto-diffs vs the PR base
  ```
- Put the resulting mermaid graph + added/removed modules/edges in the PR body
  (and/or post it as a comment with `--pr`).
- The committed `code/baseline.json` is the *accepted* structure. The
  pre-commit hook (`.githooks/pre-commit`) regenerates it on commit; the CI
  gate (`code/observe.py --check`) blocks a merge if the baseline is out of
  sync with the code. **Merging is the acceptance** of a structural change —
  so the baseline must be in sync in the PR, or CI fails.
- Install the hook once per clone: `git config core.hooksPath .githooks`.

## Quick checklist before opening a PR

- [ ] Spec change made in `tla/ReservationSystem.tla`; TLC passes; `tlc_output.txt` updated.
- [ ] Python code + tests updated to mirror the spec; `pytest -q` all green.
- [ ] State-space mirror count == TLC distinct-state count.
- [ ] `python3 code/observe.py --check` passes (baseline in sync with code).
- [ ] PR body: TLA+ delta + findings (incl. any counterexample) + structure
      graph vs the base branch.
