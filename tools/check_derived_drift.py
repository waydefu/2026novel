#!/usr/bin/env python3
"""Drift detection: 11 is derived. Rebuild is not full NLP; obvious inconsistency FAILs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import GOVERNANCE_11, OUTLINE, SETTINGS, DRAFT, split_chapters  # noqa: E402

UNSEEN = ("克蕾西雅", "瑟拉菲娜", "艾琳娜")


def drift_check(
    draft_text: str,
    gov_text: str,
    outline_text: str,
    settings_text: str,
) -> list[str]:
    errors: list[str] = []
    chapters = split_chapters(draft_text)
    if not chapters:
        return ["DRIFT: live draft has no chapter headings"]
    max_draft = max(chapters)
    facts = {int(n) for n in re.findall(r"TEXT-FACT[^\n]*Ch(?:apter)?\s*(\d+)", gov_text)}
    facts.update(int(n) for n in re.findall(r"\[TEXT-FACT Ch(\d+)", gov_text))
    facts.update(int(n) for n in re.findall(r"TEXT-FACT Ch(\d+)", gov_text))
    # also Ch5–7 / Ch1–2
    for a, b in re.findall(r"Ch(\d+)[–-](\d+)", gov_text):
        facts.update(range(int(a), int(b) + 1))
    extra = sorted(n for n in facts if n > max_draft)
    if extra:
        errors.append(f"DRIFT FAIL: 11 TEXT-FACT cites chapters not in draft: {extra}")
    cutoff = re.search(r"CUT-OFF：現行正文第([一二三四五六七八九十]+)章", gov_text)
    cn = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8}
    if cutoff:
        cut_n = cn.get(cutoff.group(1))
        if cut_n is not None and max_draft > cut_n:
            errors.append(f"DRIFT NEEDS_REVIEW: draft has Ch{max_draft} but 11 CUT-OFF is Ch{cut_n}")
    if 5 in chapters and "莉諾兒" in chapters[5]:
        errors.append("DRIFT FAIL: 莉諾兒 named in Ch5 but Knowledge says name is unknown until Ch6")
    for name in UNSEEN:
        if name in draft_text:
            errors.append(f"DRIFT NEEDS_REVIEW: {name} appears in draft while 11 K015 says not yet entered")
    if "09-P08" in outline_text and "P08" not in gov_text:
        errors.append("DRIFT FAIL: 09 has P08 but 11 does not mention P08")
    if "莉諾兒" not in settings_text:
        errors.append("DRIFT FAIL: settings missing 莉諾兒 bible")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", default=str(DRAFT))
    parser.add_argument("--gov", default=str(GOVERNANCE_11))
    parser.add_argument("--outline", default=str(OUTLINE))
    parser.add_argument("--settings", default=str(SETTINGS))
    args = parser.parse_args()
    errors = drift_check(
        Path(args.draft).read_text(encoding="utf-8"),
        Path(args.gov).read_text(encoding="utf-8"),
        Path(args.outline).read_text(encoding="utf-8"),
        Path(args.settings).read_text(encoding="utf-8"),
    )
    if errors:
        for err in errors:
            print(err)
        return 1
    print("OK\tdrift\t11 matches draft/09 headings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
