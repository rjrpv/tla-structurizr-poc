"""Observe architecture drift: diff the code's dependency graph against a baseline.

Observation, not control. This is for a project that is being bootstrapped:
we want to *see* when the code's structure changes relative to a known-good
baseline and advertise that in the PR — not block the PR. The exit code is
always 0 (unless pydeps itself fails); nothing here is a gate.

How it works
------------
1. Run ``pydeps`` on the package to get the current dependency graph (JSON).
2. Load the committed baseline (``baseline.json``) — the graph as of the last
   time we looked.
3. Diff the two: which modules and edges were added / removed.
4. Emit a short observation (markdown for humans, JSON for machines).

Usage
-----
    # print the observation for the current code
    python3 code/observe.py

    # post it as a comment on PR #N (uses $GITHUB_TOKEN)
    python3 code/observe.py --pr 2

    # after reviewing, accept the current state as the new baseline
    python3 code/observe.py --save-baseline

The baseline is a plain JSON file you own; the diff between it and the live
graph is the unit of observation.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE / "reservation"
BASELINE = HERE / "baseline.json"
PKG_PREFIX = "reservation."


def run_pydeps() -> dict:
    """Run pydeps on the package and return its dependency graph as a dict.

    ``--show-deps`` prints the dependency analysis as JSON to stdout.
    """
    cmd = [
        sys.executable, "-m", "pydeps", str(PKG),
        "--no-output", "--show-deps", "--rmprefix", "code",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"pydeps failed:\n{proc.stderr}")
    return json.loads(proc.stdout)


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


def render_markdown(diff: dict, live: dict) -> str:
    changed = any(diff[k] for k in diff)
    if not changed:
        return (
            "### Architecture observation\n\n"
            f"No structural change vs baseline — {len(live)} modules, "
            f"{sum(len(v) for v in live.values())} edges."
        )
    lines = ["### Architecture observation", "", "_Observation only — not a gate._", ""]
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
        "_To accept this as the new baseline: `python3 code/observe.py --save-baseline`_"
    )
    return "\n".join(lines)


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pr", type=int, help="post the observation as a comment on this PR")
    ap.add_argument("--dry-run", action="store_true", help="print instead of posting")
    ap.add_argument("--save-baseline", action="store_true", help="write the live graph as the new baseline")
    ap.add_argument("--json", action="store_true", help="emit the diff as JSON")
    args = ap.parse_args()

    live = normalize(run_pydeps())

    if args.save_baseline:
        BASELINE.write_text(json.dumps(live, indent=2) + "\n")
        print(f"saved baseline: {len(live)} modules, {sum(len(v) for v in live.values())} edges")
        return 0

    base = load_baseline()
    diff = diff_graph(base, live)
    md = render_markdown(diff, live)

    if args.json:
        print(json.dumps({"diff": diff, "live": live}, indent=2))
    else:
        print(md)

    if args.pr:
        post_pr_comment(args.pr, md, args.dry_run)

    # Observation mode: never block the PR.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
