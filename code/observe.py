"""Observe and accept architecture changes.

Two distinct jobs, kept separate on purpose:

* **Observation** (default, and ``--pr``): diff the live dependency graph
  against a *reference* — by default the committed baseline, or a git ref
  (``--against <ref>``), or the PR's base branch (``--pr``). This is the
  "what did this branch change structurally?" view. It never blocks.

* **Acceptance gate** (``--check``): the committed baseline must match a
  fresh generation of the graph. If the code changed but the baseline wasn't
  regenerated, this fails (non-zero exit) and blocks the merge. This is what
  makes *merging* a PR the act that accepts a structural change: the baseline
  is the record of the accepted state, and it must be in sync with the code.

The pre-commit hook (``.githooks/pre-commit``) keeps the baseline in sync
locally; the CI gate (``.github/workflows/ci.yml``) enforces it for everyone.

Usage
-----
    # diff the live graph vs the committed baseline (observation)
    python3 code/observe.py

    # the canonical examples package (RJR-275)
    python3 code/observe.py --target examples

    # diff the live graph vs a target branch (e.g. what this PR changes)
    python3 code/observe.py --against main

    # post that observation on PR #N (auto-diffs vs the PR's base branch)
    python3 code/observe.py --pr 4

    # gate: fail if any committed baseline is out of sync with the code
    python3 code/observe.py --check

    # regenerate a baseline from the current code (accept the state)
    python3 code/observe.py --save-baseline --target examples
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# The packages the observer watches. Each has its own baseline file, so the
# two graphs are tracked (and gated) independently. The names are short on
# purpose: ``--target reservation`` / ``--target examples``.
TARGETS = {
    "reservation": {
        "pkg": HERE / "reservation",
        "prefix": "reservation.",
        "rmprefix": "code",
        "baseline": HERE / "baseline.json",
        "git_path": "code/reservation",
    },
    "examples": {
        "pkg": REPO / "examples" / "code",
        "prefix": "code.",
        "rmprefix": "examples",
        "baseline": REPO / "examples" / "baseline.json",
        "git_path": "examples/code",
    },
}
DEFAULT_TARGET = "reservation"


def run_pydeps(pkg: Path, rmprefix: str) -> dict:
    """Run pydeps on a package dir and return its dependency graph as a dict."""
    cmd = [
        sys.executable, "-m", "pydeps", str(pkg),
        "--no-output", "--show-deps", "--rmprefix", rmprefix,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"pydeps failed:\n{proc.stderr}")
    return json.loads(proc.stdout)


def live_graph(target: str = DEFAULT_TARGET) -> dict:
    """The normalized dependency graph of the current working tree.

    Defaults to the reservation package so ``from observe import live_graph``
    (used by the architecture tests) keeps working unchanged.
    """
    t = TARGETS[target]
    return normalize(run_pydeps(t["pkg"], t["rmprefix"]), t["prefix"])


def graph_from_ref(ref: str, target: str = DEFAULT_TARGET) -> dict:
    """The normalized dependency graph of the package as it exists at ``ref``.

    Extracts the package from the ref into a temp dir (preserving its path so
    module names match) and runs pydeps on it. This is how we diff a branch
    against its target branch without checking it out.
    """
    t = TARGETS[target]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        tar = tmp / "pkg.tar"
        with open(tar, "wb") as fh:
            subprocess.run(
                ["git", "archive", ref, t["git_path"]],
                cwd=REPO, stdout=fh, check=True,
            )
        subprocess.run(["tar", "-x", "-f", str(tar), "-C", str(tmp)], check=True)
        return normalize(run_pydeps(tmp / t["git_path"], t["rmprefix"]), t["prefix"])


def normalize(graph: dict, prefix: str) -> dict:
    """Reduce pydeps' graph to {short_module: [short_imports]} for the package.

    Drops the ``__main__`` pseudo-module and anything outside the package.
    """
    out = {}
    for name, info in graph.items():
        if name == "__main__" or not name.startswith(prefix):
            continue
        short = name[len(prefix):]
        deps = sorted(
            dep[len(prefix):]
            for dep in info.get("imports", [])
            if dep.startswith(prefix)
        )
        out[short] = deps
    return out


def load_baseline(target: str = DEFAULT_TARGET) -> dict:
    path = TARGETS[target]["baseline"]
    if not path.exists():
        raise SystemExit(
            f"no baseline at {path}. "
            f"Run: python3 code/observe.py --save-baseline --target {target}"
        )
    return json.loads(path.read_text())


def diff_graph(base: dict, live: dict) -> dict:
    """Diff two normalized graphs. Returns added/removed modules and edges."""
    base_mods, live_mods = set(base), set(live)
    base_edges = {(m, d) for m, deps in base.items() for d in deps}
    live_edges = {(m, d) for m, deps in live.items() for d in deps}
    return {
        "modules_added": sorted(live_mods - base_mods),
        "modules_removed": sorted(base_mods - live_mods),
        "edges_added": sorted(f"{a} -> {b}" for a, b in live_edges - base_edges),
        "edges_removed": sorted(f"{a} -> {b}" for a, b in base_edges - live_edges),
    }


def render_mermaid(diff: dict, live: dict) -> str:
    """Render the live dependency graph as a mermaid diagram.

    Every module is declared as a node (so isolated modules with no edges
    still show up), then the dependency edges are drawn. Added
    modules/edges (vs the reference) are highlighted so the structural delta
    is visible at a glance. GitHub renders ```mermaid blocks natively.
    """
    added_mods = set(diff["modules_added"])
    added_edges = {tuple(e.split(" -> ")) for e in diff["edges_added"]}
    lines = ["```mermaid", "graph LR"]
    # Declare every node up front so modules with no edges are still drawn.
    for m in sorted(live):
        lines.append(f"    {m}[{m}]")
    link_index = {}  # (from, to) -> declaration index (mermaid linkStyle needs this)
    for m, deps in sorted(live.items()):
        for d in deps:
            link_index[(m, d)] = len(link_index)
            lines.append(f"    {m} --> {d}")
    lines.append("    classDef added fill:#12261e,stroke:#3fb950,color:#3fb950,stroke-width:2px")
    for m in sorted(added_mods):
        lines.append(f"    class {m} added")
    for (a, b), idx in sorted(link_index.items(), key=lambda kv: kv[1]):
        if (a, b) in added_edges:
            lines.append(f"    linkStyle {idx} stroke:#3fb950,stroke-width:2px")
    lines.append("```")
    return "\n".join(lines)


def render_markdown(diff: dict, live: dict, against: str) -> str:
    changed = any(diff[k] for k in diff)
    if not changed:
        return (
            f"### Architecture observation\n\n"
            f"No structural change vs {against} — {len(live)} modules, "
            f"{sum(len(v) for v in live.values())} edges."
        )
    lines = [f"### Architecture observation (vs {against})", "",
             "_Observation only — not a gate. Merging accepts the change._", ""]
    lines.append(render_mermaid(diff, live))
    lines.append("")
    if diff["modules_added"]:
        lines.append("**New modules**")
        lines += [f"- `{m}`" for m in diff["modules_added"]]
        lines.append("")
    if diff["modules_removed"]:
        lines.append("**Removed modules**")
        lines += [f"- `{m}`" for m in diff["modules_removed"]]
        lines.append("")
    if diff["edges_added"]:
        lines.append("**New dependencies**")
        lines += [f"- `{e}`" for e in diff["edges_added"]]
        lines.append("")
    if diff["edges_removed"]:
        lines.append("**Removed dependencies**")
        lines += [f"- `{e}`" for e in diff["edges_removed"]]
        lines.append("")
    lines.append(
        "_The baseline is regenerated on commit (pre-commit hook) and must stay "
        "in sync with the code (CI `--check` gate) — merging is the acceptance._"
    )
    return "\n".join(lines)


def pr_base_ref(pr_number: int) -> str:
    """Look up a PR's base branch via the GitHub API (for --pr auto-diff)."""
    import urllib.request

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN not set (or use --against <ref>)")
    repo = os.environ.get("OBSERVE_REPO", "rjrpv/tla-structurizr-poc")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)["base"]["ref"]


def post_pr_comment(pr_number: int, body: str, dry_run: bool) -> None:
    if dry_run:
        print("[dry-run] would post PR comment:\n")
        print(body)
        return
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN not set (or use --dry-run)")
    repo = os.environ.get("OBSERVE_REPO", "rjrpv/tla-structurizr-poc")
    import urllib.request

    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        d = json.load(r)
        print(f"posted comment -> {d['html_url']}")


def resolve_reference(args, target: str) -> tuple:
    """Return (reference_graph, label) for the observation diff.

    Priority: --against <ref> > --pr <n> (PR's base branch) > committed baseline.
    """
    if args.against:
        return graph_from_ref(args.against, target), args.against
    if args.pr:
        base = pr_base_ref(args.pr)
        return graph_from_ref(base, target), base
    return load_baseline(target), "baseline"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", choices=sorted(TARGETS), default=DEFAULT_TARGET,
                    help="which package to watch (default: reservation)")
    ap.add_argument("--against", metavar="REF",
                    help="diff the live graph against this git ref (e.g. main)")
    ap.add_argument("--pr", type=int,
                    help="post the observation on PR #N (auto-diffs vs the PR's base branch)")
    ap.add_argument("--dry-run", action="store_true", help="print instead of posting")
    ap.add_argument("--check", action="store_true",
                    help="gate: fail if the committed baseline is out of sync with the code")
    ap.add_argument("--save-baseline", action="store_true",
                    help="write the live graph as the new baseline (accept the state)")
    ap.add_argument("--json", action="store_true", help="emit the diff as JSON")
    ap.add_argument("--graph", action="store_true",
                    help="render the full live dependency graph as mermaid "
                         "(always, even when there is no structural change)")
    args = ap.parse_args()

    live = live_graph(args.target)

    if args.graph:
        print(render_mermaid(diff_graph({}, live), live))
        return 0

    if args.save_baseline:
        path = TARGETS[args.target]["baseline"]
        path.write_text(json.dumps(live, indent=2) + "\n")
        print(f"saved baseline ({args.target}): {len(live)} modules, "
              f"{sum(len(v) for v in live.values())} edges")
        return 0

    if args.check:
        # The gate covers every watched target, so a stale baseline in either
        # package blocks the merge.
        failed = False
        for name in TARGETS:
            g = live_graph(name)
            base = load_baseline(name)
            if base == g:
                print(f"[{name}] baseline in sync with code — {len(g)} modules, "
                      f"{sum(len(v) for v in g.values())} edges.")
            else:
                failed = True
                print(f"[{name}] baseline is OUT OF SYNC with the code.\n")
                print(render_markdown(diff_graph(base, g), g, "baseline"))
                print(f"\n  python3 code/observe.py --save-baseline --target {name}")
        return 1 if failed else 0

    ref_graph, label = resolve_reference(args, args.target)
    diff = diff_graph(ref_graph, live)
    md = render_markdown(diff, live, label)

    if args.json:
        print(json.dumps({"against": label, "diff": diff, "live": live}, indent=2))
    else:
        print(md)

    if args.pr:
        post_pr_comment(args.pr, md, args.dry_run)

    # Observation mode: never block the PR.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
