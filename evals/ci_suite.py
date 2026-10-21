#!/usr/bin/env python3
"""CI entry: run gates, then write base/head/tested evidence. Fail-closed."""

from __future__ import annotations

import json
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
        "canon_contract": "FAIL",
        "rule_budget": "FAIL",
        "rule_sync": "FAIL",
        "lexicon_lock": "FAIL",
        "skills": "FAIL",
        "skill_mirror": "FAIL",
        "core_invariants": "FAIL",
        "append_only": "SKIP",
        "candidates": "SKIP",
    }

    if run([PY, str(ROOT / "tools" / "scan_hard_gate.py")]) != 0:
        _evidence(results, git_base)
        return 1
    results["hard_gate"] = "PASS"

    if run([PY, str(ROOT / "tools" / "canon_contract.py")]) != 0:
        _evidence(results, git_base)
        return 1
    results["canon_contract"] = "PASS"

    if run([PY, str(ROOT / "tools" / "check_rule_budget.py")]) != 0:
        _evidence(results, git_base)
        return 1
    results["rule_budget"] = "PASS"

    if run([PY, str(ROOT / "tools" / "sync_agent_rules.py"), "--check"]) != 0:
        _evidence(results, git_base)
        return 1
    results["rule_sync"] = "PASS"

    if run([PY, str(ROOT / "tools" / "prose_lexicon.py"), "--check-lock"]) != 0:
        _evidence(results, git_base)
        return 1
    results["lexicon_lock"] = "PASS"

    if run([PY, str(ROOT / "tools" / "validate_skills.py")]) != 0:
        _evidence(results, git_base)
        return 1
    results["skills"] = "PASS"

    if run([PY, str(ROOT / "tools" / "sync_skills.py"), "--check"]) != 0:
        _evidence(results, git_base)
        return 1
    results["skill_mirror"] = "PASS"

    if run([PY, str(ROOT / "tools" / "check_core_invariants.py")]) != 0:
        _evidence(results, git_base)
        return 1
    results["core_invariants"] = "PASS"

    # Base-relative checks: contracts and the rule registry are append-only.
    if git_base:
        if run([PY, str(ROOT / "tools" / "canon_contract.py"), "--base", git_base]) != 0:
            _evidence(results, git_base)
            return 1
        if run([PY, str(ROOT / "tools" / "check_rule_budget.py"), "--base", git_base]) != 0:
            _evidence(results, git_base)
            return 1
    results["append_only"] = "PASS"

    # Candidate scans: informational. They report, they do not judge.
    for tool in ("scan_pattern_risk.py", "prose_lexicon.py", "prose_rhythm.py"):
        run([PY, str(ROOT / "tools" / tool)])
    run([PY, str(ROOT / "tools" / "style_profile.py"), str(ROOT / "10_現行創作資料" / "小說正文第三版.md")])
    results["candidates"] = "REPORTED"

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

    return _evidence(results, git_base)


def _evidence(results: dict[str, str], git_base: str) -> int:
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
        "--canon-contract",
        results["canon_contract"],
        "--rule-budget",
        results["rule_budget"],
        "--rule-sync",
        results["rule_sync"],
        "--lexicon-lock",
        results["lexicon_lock"],
        "--skills",
        results["skills"],
        "--skill-mirror",
        results["skill_mirror"],
        "--core-invariants",
        results["core_invariants"],
        "--append-only",
        results["append_only"],
        "--candidates",
        results["candidates"],
        "--out",
        str(out),
    ]
    if git_base:
        cmd.extend(["--base-sha", git_base])
    if run(cmd) != 0:
        print("ERROR\tevidence\twrite_evidence.py failed", file=sys.stderr)
        return 1
    # Fail closed: the evidence file must exist, be valid JSON, carry the SHA
    # binding and every gate result. A missing or malformed evidence file means
    # the run is not verifiable — that has to fail the job, not pass it.
    try:
        payload = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR\tevidence\tunreadable evidence {out}: {exc}", file=sys.stderr)
        return 1
    required = ("head_sha", "tested_sha", "tested_ref_type", "eval_version")
    # A base is only meaningful when it is a real sha: a push to a brand-new
    # branch reports before=0000..., which must not be demanded as evidence.
    env_base = os.environ.get("EVIDENCE_BASE_SHA", "").strip()
    if env_base and set(env_base) != {"0"}:
        required = required + ("base_sha",)
    missing = [k for k in required if not payload.get(k)]
    if missing:
        print(f"ERROR\tevidence\tmissing fields {missing} in {out}", file=sys.stderr)
        return 1
    for gate in ("hard_gate", "canon_contract", "rule_budget", "rule_sync", "lexicon_lock", "skills", "skill_mirror", "core_invariants", "regression"):
        if payload.get(gate) not in {"PASS", "REPORTED"}:
            print(f"ERROR\tevidence\tgate {gate}={payload.get(gate)}", file=sys.stderr)
            return 1
    expected = os.environ.get("EVIDENCE_TESTED_SHA") or os.environ.get("GITHUB_SHA")
    if expected and payload.get("tested_sha") != expected:
        print(f"ERROR\tevidence\ttested_sha mismatch: {payload.get('tested_sha')} != {expected}", file=sys.stderr)
        return 1
    print(f"OK\tevidence\t{out.name}\ttested={payload['tested_sha'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
