#!/usr/bin/env python3
"""CI entry: run gates, then write base/head/tested evidence. Fail-closed."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(args: list[str]) -> int:
    print("+", " ".join(args), flush=True)
    return subprocess.call(args, cwd=ROOT)


def main() -> int:
    git_base = ""
    if "--git-base" in sys.argv:
        git_base = sys.argv[sys.argv.index("--git-base") + 1]

    results = {
        "hard_gate": "FAIL",
        "regression": "FAIL",
        "negative_control": "FAIL",
        "revision_gate": "SKIP",
        "compiler": "FAIL",
        "drift": "FAIL",
        "recovery": "FAIL",
    }

    if run([PY, str(ROOT / "tools" / "scan_hard_gate.py")]) != 0:
        _evidence(results, git_base)
        return 1
    results["hard_gate"] = "PASS"

    if run([PY, str(ROOT / "evals" / "run_evals.py")]) != 0:
        _evidence(results, git_base)
        return 1
    results["regression"] = "PASS"
    results["negative_control"] = "PASS"
    results["recovery"] = "PASS"

    if run([PY, str(ROOT / "tools" / "compile_context.py"), "--target", "P08", "--check-only"]) != 0:
        _evidence(results, git_base)
        return 1
    results["compiler"] = "PASS"

    if run([PY, str(ROOT / "tools" / "check_derived_drift.py")]) != 0:
        _evidence(results, git_base)
        return 1
    results["drift"] = "PASS"

    if git_base:
        code = run(
            [
                PY,
                str(ROOT / "tools" / "check_revision_gate.py"),
                "--manifest",
                str(ROOT / "governance" / "change-manifest.yaml"),
                "--git-base",
                git_base,
            ]
        )
        results["revision_gate"] = "PASS" if code == 0 else "FAIL"
        if code != 0:
            _evidence(results, git_base)
            return 1
    else:
        code = run(
            [
                PY,
                str(ROOT / "tools" / "check_revision_gate.py"),
                "--manifest",
                str(ROOT / "governance" / "change-manifest.yaml"),
            ]
        )
        results["revision_gate"] = "PASS" if code == 0 else "FAIL"
        if code != 0:
            _evidence(results, git_base)
            return 1

    _evidence(results, git_base)
    return 0


def _evidence(results: dict[str, str], git_base: str) -> None:
    tested = os.environ.get("EVIDENCE_TESTED_SHA") or os.environ.get("GITHUB_SHA") or "local"
    out = ROOT / "governance" / "evidence" / f"{tested}.json"
    cmd = [
        PY,
        str(ROOT / "tools" / "write_evidence.py"),
        "--hard-gate",
        results["hard_gate"],
        "--regression",
        results["regression"],
        "--negative-control",
        results["negative_control"],
        "--revision-gate",
        results["revision_gate"],
        "--compiler",
        results["compiler"],
        "--drift",
        results["drift"],
        "--recovery",
        results["recovery"],
        "--out",
        str(out),
    ]
    if git_base:
        cmd.extend(["--base-sha", git_base])
    run(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
