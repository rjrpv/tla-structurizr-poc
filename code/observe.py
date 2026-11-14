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

    # diff the live graph vs a target branch (e.g. what this PR changes)
    python3 code/observe.py --against main

    # post that observation on PR #N (auto-diffs vs the PR's base branch)
    python3 code/observe.py --pr 4

    # gate: fail if the committed baseline is out of sync with the code
    python3 code/observe.py --check

    # regenerate the baseline from the current code (accept the state)
    python3 code/observe.py --save-baseline
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
PKG = HERE / "reservation"
BASELINE = HERE / "baseline.json"
PKG_PREFIX = "reservation."


def run_pydeps(pkg: Path) -> dict:
    """Run pydeps on a package dir and return its dependency graph as a dict."""
    cmd = [
        sys.executable, "-m", "pydeps", str(pkg),
        "--no-output", "--show-deps", "--rmprefix", "code",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"pydeps failed:\n{proc.stderr}")
    return json.loads(proc.stdout)


def live_graph() -> dict:
    """The normalized dependency graph of the current working tree."""
    return normalize(run_pydeps(PKG))


def graph_from_ref(ref: str) -> dict:
    """The normalized dependency graph of the package as it exists at ``ref``.

    Extracts ``code/reservation`` from the ref into a temp dir (preserving the
    ``code/`` prefix so module names match) and runs pydeps on it. This is how
    we diff a branch against its target branch without checking it out.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        tar = tmp / "pkg.tar"
        with open(tar, "wb") as fh:
            subprocess.run(
                ["git", "archive", ref, "code/reservation"],
                cwd=REPO, stdout=fh, check=True,
            )
        subprocess.run(["tar", "-x", "-f", str(tar), "-C", str(tmp)], check=True)
        return normalize(run_pydeps(tmp / "code" / "reservation"))


def normalize(graph: dict) -> dict:
    """Reduce pydeps' graph to {short_module: [short_imports]} for the package.

    Drops the ``__main__`` pseudo-module and anything outside the package.
    """
    out = {}
    for name, info in graph.items():
        if name == "__main__" or not name.startswith(PKG_PREFIX):
            continue
        short = name[len(PKG_PREFIX):]
        deps = sorted(
            dep[len(PKG_PREFIX):]
            for dep in info.get("imports", [])
            if dep.startswith(PKG_PREFIX)
        )
        out[short] = deps
    return out


def load_baseline() -> dict:
    if not BASELINE.exists():
        raise SystemExit(
            f"no baseline at {BASELINE}. Run: python3 code/observe.py --save-baseline"
        )
    return json.loads(BASELINE.read_text())


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

    Added modules/edges (vs the reference) are highlighted so the structural
    delta is visible at a glance. GitHub renders ```mermaid blocks natively.
    """
    added_mods = set(diff["modules_added"])
    added_edges = {tuple(e.split(" -> ")) for e in diff["edges_added"]}
    lines = ["```mermaid", "graph LR"]
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


def resolve_reference(args) -> tuple:
    """Return (reference_graph, label) for the observation diff.

    Priority: --against <ref> > --pr <n> (PR's base branch) > committed baseline.
    """
    if args.against:
        return graph_from_ref(args.against), args.against
    if args.pr:
        base = pr_base_ref(args.pr)
        return graph_from_ref(base), base
    return load_baseline(), "baseline"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
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
    args = ap.parse_args()

    live = live_graph()

    if args.save_baseline:
        BASELINE.write_text(json.dumps(live, indent=2) + "\n")
        print(f"saved baseline: {len(live)} modules, {sum(len(v) for v in live.values())} edges")
        return 0

    if args.check:
        base = load_baseline()
        if base == live:
            print(f"baseline in sync with code — {len(live)} modules, "
                  f"{sum(len(v) for v in live.values())} edges.")
            return 0
        diff = diff_graph(base, live)
        print("baseline is OUT OF SYNC with the code. Regenerate it:\n")
        print(render_markdown(diff, live, "baseline"))
        print("\n  python3 code/observe.py --save-baseline")
        return 1

    ref_graph, label = resolve_reference(args)
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
