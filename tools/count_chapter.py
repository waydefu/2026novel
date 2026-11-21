#!/usr/bin/env python3
"""Count CJK characters in a live-draft chapter (or all chapters). Informational only."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT, CHAPTER_HEAD, chapter_number, count_zh_chars, split_chapters  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int, default=0, help="Chapter number (omit or 0 for all chapters)")
    parser.add_argument("--all", action="store_true", help="Count all chapters and print total")
    parser.add_argument("path", nargs="?", default=str(DRAFT))
    args = parser.parse_args()
    path = Path(args.path)
    text = path.read_text(encoding="utf-8")
    chapters = split_chapters(text)
    titles: dict[int, str] = {}
    for m in CHAPTER_HEAD.finditer(text):
        cn = chapter_number(m.group(1))
        if cn is not None:
            titles[cn] = f"第{m.group(1)}章｜{m.group(2)}"

    if args.all or args.chapter == 0:
        total = 0
        for num in sorted(chapters):
            n = count_zh_chars(chapters[num])
            total += n
            print(f"CHAPTER\t{num}\t{titles.get(num, '')}\tZH_CHARS\t{n}")
        print(f"TOTAL\tCHAPTERS={len(chapters)}\tZH_CHARS\t{total}")
        return 0

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
