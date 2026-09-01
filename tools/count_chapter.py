#!/usr/bin/env python3
"""Count CJK characters in a live-draft chapter. Informational only."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT, count_zh_chars, split_chapters  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("path", nargs="?", default=str(DRAFT))
    args = parser.parse_args()
    path = Path(args.path)
    text = path.read_text(encoding="utf-8")
    chapters = split_chapters(text)
    body = chapters.get(args.chapter)
    if body is None:
        print(f"ERROR\tchapter {args.chapter} not found", file=sys.stderr)
        print("available:", ", ".join(str(n) for n in sorted(chapters)))
        return 2
    n = count_zh_chars(body)
    print(f"CHAPTER\t{args.chapter}\tZH_CHARS\t{n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
