"""Architecture well-formedness tests (observation mode).

Structurizr is gone — the architecture is now *observed* with pydeps
(``code/observe.py``) against a committed baseline, not enforced against a
hand-written model. So these tests no longer assert a specific intended
dependency structure. They only catch what is *always* a defect, plus one
hygiene check:

  * the module dependency graph is a DAG (no import cycles)
  * the system wires all four modules
  * the committed baseline (``code/baseline.json``) matches the live graph —
    i.e. the code hasn't drifted from the last observed state. If it has,
    the test points you at ``observe.py --save-baseline`` to accept it.

This is "course-correct, not control": it flags drift, it doesn't forbid it.
"""

import json
import re
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
PKG = CODE_DIR / "reservation"
BASELINE = CODE_DIR / "baseline.json"
sys.path.insert(0, str(CODE_DIR))  # so we can reuse observe.py's graph helpers

# module filename -> the set of sibling modules it imports
IMPORT_GRAPH = {}
for py in sorted(PKG.glob("*.py")):
    if py.name == "__init__.py":
        continue
    text = py.read_text()
    deps = set()
    for m in re.finditer(r"^\s*from\s+\.\s*(\w+)\s+import", text, re.MULTILINE):
        deps.add(m.group(1))
    for m in re.finditer(r"^\s*import\s+(\w+)\s*$", text, re.MULTILINE):
        # only sibling modules count; ignore stdlib / third-party
        if (PKG / f"{m.group(1)}.py").exists():
            deps.add(m.group(1))
    IMPORT_GRAPH[py.stem] = deps


def test_no_dependency_cycles():
    """The module dependency graph must be a DAG (no import cycles)."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {m: WHITE for m in IMPORT_GRAPH}

    def visit(node):
        color[node] = GRAY
        for dep in IMPORT_GRAPH[node]:
            if color[dep] == GRAY:
                raise AssertionError(f"import cycle through {node} -> {dep}")
            if color[dep] == WHITE:
                visit(dep)
        color[node] = BLACK

    for m in IMPORT_GRAPH:
        if color[m] == WHITE:
            visit(m)


def test_system_wires_all_four_modules():
    """ReservationSystem composes all four modules (intake, serving, inventory, ledger)."""
    text = (PKG / "system.py").read_text()
    for mod in ("Inventory", "RequestIntake", "Ledger", "ServingLogic"):
        assert mod in text, f"system.py must wire the {mod} module"


def test_baseline_matches_live_graph():
    """The committed baseline must match the code's current dependency graph.

    This is the observation-mode hygiene check: it doesn't forbid the code
    from changing, it just makes sure the baseline (what we last observed)
    is in sync. If the code moved, run ``python3 code/observe.py --save-baseline``.
    """
    import pytest

    from observe import normalize, run_pydeps

    try:
        live = normalize(run_pydeps())
    except SystemExit:
        pytest.skip("pydeps not installed; can't compute the live graph")
    if not BASELINE.exists():
        raise AssertionError("code/baseline.json missing; run: python3 code/observe.py --save-baseline")
    base = json.loads(BASELINE.read_text())
    assert base == live, (
        "code has drifted from the committed baseline.\n"
        f"  baseline: {json.dumps(base, sort_keys=True)}\n"
        f"  live:     {json.dumps(live, sort_keys=True)}\n"
        "Accept the change: python3 code/observe.py --save-baseline"
    )
