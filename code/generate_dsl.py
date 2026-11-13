"""Generate a Structurizr DSL model FROM the Python code.

This is the "flip" of the PoC: instead of hand-writing the architecture and
implementing it, we statically analyze ``code/reservation/`` and derive the
architecture model from the code.

It reads, for each module:
  * the class it defines  ->  a container (name derived from the class)
  * its ``from .X import`` ->  a dependency relationship to module X

and emits a valid Structurizr workspace (system context + container view) to
``structurizr/generated_from_code.dsl``.

Run it:
    python3 code/generate_dsl.py

Then validate the result:
    structurizr validate -w structurizr/generated_from_code.dsl

Because the model is *derived* from the code, it cannot drift: change the
imports and re-run, and the model changes with them. (The hand-written
``structurizr/reservation.dsl`` is the "intended" model; this generated one is
the "actual" model — diffing the two is the drift check.)
"""

import re
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent / "reservation"
OUT = Path(__file__).resolve().parents[1] / "structurizr" / "generated_from_code.dsl"


def camel_to_title(name: str) -> str:
    """RequestIntake -> 'Request Intake'."""
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name)


def first_class(text: str):
    m = re.search(r"^class\s+([A-Za-z_]\w*)", text, re.MULTILINE)
    return m.group(1) if m else None


def imports_of(text: str):
    """Yield sibling module names from ``from .X import ...`` statements."""
    for m in re.finditer(r"^\s*from\s+\.\s*(\w+)\s+import", text, re.MULTILINE):
        yield m.group(1)


def main() -> int:
    modules = {}
    for py in sorted(PKG.glob("*.py")):
        if py.name == "__init__.py":
            continue
        text = py.read_text()
        cls = first_class(text)
        if cls is None:
            continue
        modules[py.stem] = {
            "class": cls,
            "name": camel_to_title(cls),
            "imports": sorted(imports_of(text)),
        }

    # The software system is the module that wires the others (system.py).
    system_mod = "system"
    if system_mod not in modules:
        print("error: system.py not found", file=sys.stderr)
        return 1
    system_name = modules[system_mod]["name"]
    containers = {m: info for m, info in modules.items() if m != system_mod}

    # Relationships: container -> (target container, description).
    edges = []
    for mod, info in containers.items():
        for dep in info["imports"]:
            if dep in containers:
                edges.append((mod, dep))

    lines = []
    lines.append(f'workspace "ReservationSystem (generated from code)" "Derived from code/reservation" {{')
    lines.append("    model {")
    lines.append('        customers = person "Customers"')
    lines.append(f'        reservation = softwareSystem "{system_name}" {{')
    for mod, info in containers.items():
        lines.append(f'            {mod} = container "{info["name"]}" "Python module {mod}.py ({info["class"]})"')
    lines.append("        }")
    lines.append('        customers -> reservation "requests a ticket"')
    for src, dst in edges:
        lines.append(f'        {src} -> {dst} "imports"')
    lines.append("    }")
    lines.append("    views {")
    lines.append('        systemContext reservation "generated-context" {')
    lines.append("            include *")
    lines.append("        }")
    lines.append('        container reservation "generated-container" {')
    lines.append("            include *")
    lines.append("        }")
    lines.append("    }")
    lines.append("}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}")
    print(f"  system: {system_name}")
    print(f"  containers: {', '.join(info['name'] for info in containers.values())}")
    print(f"  relationships: {len(edges)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
