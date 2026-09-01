#!/usr/bin/env python3
"""Scan PATTERN RISK candidates. Always exit 0 unless --fail-on-hits (evals only)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT, scan_pattern_risk  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DRAFT))
    parser.add_argument("--fail-on-hits", action="store_true")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.is_file():
        print(f"ERROR\tmissing file\t{path}", file=sys.stderr)
        return 2
    hits = scan_pattern_risk(path)
    for hit in hits:
        print(hit.format())
    print(f"CANDIDATES\t{len(hits)}\t{path}")
    print("NOTE\t這些是候選，須依 AGENTS.md §13 人工判定；零命中不等于通過。")
    if args.fail_on_hits and hits:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
