"""Architecture test: the code's structure matches the Structurizr model.

This is the structural analogue of the TLA+ invariant (the Python equivalent
of an ArchUnit / NDepend rule). It statically inspects the imports in
``code/reservation/`` and asserts the dependency direction matches the
relationships declared in ``structurizr/reservation.dsl``:

    intake    -> serving     (RequestIntake drives ServingLogic)
    serving   -> inventory   (ServingLogic reads/decrements Inventory)
    serving   -> ledger      (ServingLogic records in the Ledger)

and that the "data" containers (inventory, ledger) do not depend back on the
logic — i.e. no cycles and no inverted dependencies.
"""

import re
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "reservation"

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


def test_intake_depends_on_serving():
    assert "serving" in IMPORT_GRAPH["intake"], (
        f"RequestIntake must depend on ServingLogic (intake -> serving); got {IMPORT_GRAPH['intake']}"
    )


def test_serving_depends_on_inventory_and_ledger():
    assert {"inventory", "ledger"} <= IMPORT_GRAPH["serving"], (
        f"ServingLogic must depend on inventory and ledger; got {IMPORT_GRAPH['serving']}"
    )
    # Serving is a pure decision: it must NOT depend on intake (no cycle).
    assert "intake" not in IMPORT_GRAPH["serving"], (
        f"ServingLogic must not depend on RequestIntake (would create a cycle); got {IMPORT_GRAPH['serving']}"
    )


def test_data_containers_are_dependency_free():
    """inventory and ledger are data stores; they must not import any logic."""
    assert IMPORT_GRAPH["inventory"] == set(), f"Inventory must be dependency-free; got {IMPORT_GRAPH['inventory']}"
    assert IMPORT_GRAPH["ledger"] == set(), f"Ledger must be dependency-free; got {IMPORT_GRAPH['ledger']}"


def test_no_dependency_cycles():
    """The container dependency graph must be a DAG (no cycles)."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {m: WHITE for m in IMPORT_GRAPH}

    def visit(node):
        color[node] = GRAY
        for dep in IMPORT_GRAPH[node]:
            if color[dep] == GRAY:
                raise AssertionError(f"dependency cycle through {node} -> {dep}")
            if color[dep] == WHITE:
                visit(dep)
        color[node] = BLACK

    for m in IMPORT_GRAPH:
        if color[m] == WHITE:
            visit(m)


def test_system_wires_all_four_containers():
    """ReservationSystem composes all four containers (the 'software system')."""
    text = (PKG / "system.py").read_text()
    for container in ("Inventory", "RequestIntake", "Ledger", "ServingLogic"):
        assert container in text, f"system.py must wire the {container} container"
