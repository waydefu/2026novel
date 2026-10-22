#!/usr/bin/env python3
"""Scan HARD GATE issues. Default: live draft only. Path-aware; backups/changelog/11 are exempt.

Governance rules enforced here (registry: governance/rule-budget.json):
    HB-001  正文不得出現 TBD 標籤或 TBD 編號
    HB-002  讀者可見章名不得使用 P-0N 形式
    HB-003  姓名統一寫作「亞德里安・梵恩」
    HB-027  正文不得混入簡體字（繁體稿）
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT, classify_path, scan_hard_gate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DRAFT))
    parser.add_argument("--force", action="store_true", help="Ignore path scope (evals only)")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.is_file():
        print(f"ERROR\tmissing file\t{path}", file=sys.stderr)
        return 2
    scope = classify_path(path)
    if scope != "prose" and not args.force:
        print(f"EXEMPT\tscope={scope}\t{path}")
        return 0
    try:
        hits = scan_hard_gate(path, force_scope="prose" if args.force else None)
    except UnicodeDecodeError:
        print(f"HARD\tencoding\t{path}\tnot UTF-8", file=sys.stderr)
        return 1
    for hit in hits:
        print(hit.format())
    if hits:
        print(f"{len(hits)} hard-gate hit(s)", file=sys.stderr)
        return 1
    print("OK\thard-gate\t0 hits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
