#!/usr/bin/env python3
"""Scan HARD GATE issues. Default: live draft only. Path-aware; backups/changelog/11 are exempt."""

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
