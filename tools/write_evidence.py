#!/usr/bin/env python3
"""Write commit-bound evidence. SHA in the file must match the git commit that produced it."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import ROOT  # noqa: E402

EVAL_VERSION_PATH = ROOT / "evals" / "VERSION"


def git_sha() -> str:
    env_sha = (
        __import__("os").environ.get("GITHUB_SHA")
        or __import__("os").environ.get("EVIDENCE_SHA")
        or ""
    )
    if env_sha:
        return env_sha
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
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    sha = git_sha()
    version = EVAL_VERSION_PATH.read_text(encoding="utf-8").strip() if EVAL_VERSION_PATH.is_file() else "unknown"
    payload = {
        "commit": sha,
        "eval_version": version,
        "hard_gate": args.hard_gate,
        "regression": args.regression,
        "negative_control": args.negative_control,
        "revision_gate": args.revision_gate,
        "compiler": args.compiler,
        "drift": args.drift,
        "recovery": args.recovery,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bound": f"evidence is valid only for commit {sha}",
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
