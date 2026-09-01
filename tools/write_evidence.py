#!/usr/bin/env python3
"""Write SHA-bound evidence. Bind base / head / tested, not a single ambiguous github.sha."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import ROOT  # noqa: E402

EVAL_VERSION_PATH = ROOT / "evals" / "VERSION"


def _sha(*keys: str, fallback: str = "") -> str:
    for key in keys:
        val = os.environ.get(key, "").strip()
        if val and val != "0000000000000000000000000000000000000000":
            return val
    return fallback


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hard-gate", required=True)
    parser.add_argument("--regression", required=True)
    parser.add_argument("--negative-control", required=True)
    parser.add_argument("--revision-gate", default="SKIP")
    parser.add_argument("--compiler", default="SKIP")
    parser.add_argument("--drift", default="SKIP")
    parser.add_argument("--recovery", default="SKIP")
    parser.add_argument("--base-sha", default="")
    parser.add_argument("--head-sha", default="")
    parser.add_argument("--tested-sha", default="")
    parser.add_argument("--tested-ref-type", default="")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    tested = args.tested_sha or _sha("EVIDENCE_TESTED_SHA", "GITHUB_SHA", fallback=git_head())
    head = args.head_sha or _sha("EVIDENCE_HEAD_SHA", fallback=tested)
    base = args.base_sha or _sha("EVIDENCE_BASE_SHA")
    ref_type = args.tested_ref_type or os.environ.get("EVIDENCE_TESTED_REF_TYPE") or (
        "pull_request_merge_candidate"
        if os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
        else "push_head"
        if os.environ.get("GITHUB_ACTIONS")
        else "local"
    )
    version = EVAL_VERSION_PATH.read_text(encoding="utf-8").strip() if EVAL_VERSION_PATH.is_file() else "unknown"
    payload = {
        "base_sha": base,
        "head_sha": head,
        "tested_sha": tested,
        "tested_ref_type": ref_type,
        "commit": tested,
        "eval_version": version,
        "hard_gate": args.hard_gate,
        "regression": args.regression,
        "negative_control": args.negative_control,
        "revision_gate": args.revision_gate,
        "compiler": args.compiler,
        "drift": args.drift,
        "recovery": args.recovery,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bound": (
            f"evidence verifies tested_sha {tested} "
            f"(head {head} vs base {base or 'unknown'}, type={ref_type})"
        ),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"WROTE\t{out}")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
