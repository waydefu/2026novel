#!/usr/bin/env python3
"""Timeline probe: an inventory of the book's time markers.

Why this exists
---------------
The per-chapter optimisation pass revised every chapter in isolation, and
nothing checked whether the clock still moves forward across the book. This
probe lists every season, month and age statement per chapter, with enough
context to judge it by eye.

It is a **report**, not a gate. Literary text mentions seasons retrospectively
("冬天不暖" about a room, "夏天那件衣服" about a garment), so a machine rule
about season order would cry wolf. What it does flag is:

* a chapter whose season markers are not in calendar order *within* the chapter
  — which usually means a retrospective reference, and is worth a glance;
* an age inventory, so a character's age can be checked across chapters.

Usage:
    py -3 tools/timeline_probe.py
    py -3 tools/timeline_probe.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT  # noqa: E402

SEASON_CHARS = ("春", "夏", "秋", "冬")
SEASON_ORDER = {"春": 0, "夏": 1, "秋": 2, "冬": 3}

SEASON_RE = re.compile(
    r"(初春|仲春|暮春|晚春|早春|初夏|盛夏|晚夏|初秋|深秋|晚秋|入秋|初冬|深冬|晚冬|隆冬"
    r"|臘月|冬天|夏天|春天|秋天|冬|春|夏|秋)"
)
MONTH_RE = re.compile(
    r"(正月|二月|三月|四月|五月|六月|七月|八月|九月|十月|冬月|臘月|十一月|十二月"
    r"|[一二三四五六七八九十]{1,3}月)"
)
AGE_RE = re.compile(r"([一二三四五六七八九十百零]{1,3})歲")

CN_NUM = {
    "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
    "八": 8, "九": 9, "十": 10, "百": 100,
}


def cn_to_int(s: str) -> int | None:
    if not s:
        return None
    if s.isdigit():
        return int(s)
    if "十" in s:
        left, _, right = s.partition("十")
        total = (CN_NUM.get(left, 1) if left else 1) * 10
        if right:
            total += CN_NUM.get(right, 0)
        return total
    return CN_NUM.get(s) or None


def base_season(token: str) -> str | None:
    """'初冬' -> '冬', '秋天' -> '秋' (the season char is not always last)."""
    for ch in SEASON_CHARS:
        if ch in token:
            return ch
    return None


def chapter_map(text: str) -> dict[str, str]:
    parts = re.split(r"(?m)^(# 第[一二三四五六七八九十百]+章.*)$", text)
    out: dict[str, str] = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        out[name] = body
    return out


def context(body: str, start: int, end: int, pad: int = 24) -> str:
    s = max(0, start - pad)
    e = min(len(body), end + pad)
    return body[s:e].replace("\n", " ").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--draft", default=str(DRAFT))
    args = parser.parse_args()

    text = Path(args.draft).read_text(encoding="utf-8")
    chapters = chapter_map(text)

    rows: list[dict] = []
    notes: list[str] = []

    for name, body in chapters.items():
        label = name.replace("# ", "")
        seasons = []
        for m in SEASON_RE.finditer(body):
            token = m.group(1)
            base = base_season(token)
            seasons.append({
                "token": token,
                "season": base,
                "context": context(body, m.start(), m.end()),
            })
        months = sorted({m.group(1) for m in MONTH_RE.finditer(body)})
        ages = []
        for m in AGE_RE.finditer(body):
            n = cn_to_int(m.group(1))
            if n is None:
                continue
            ages.append({"age": n, "context": context(body, m.start(), m.end(), 32)})

        # calendar order inside one chapter (retrospective mentions show up here)
        order = [s["season"] for s in seasons if s["season"]]
        if order != sorted(order):
            seen = []
            for s in seasons:
                if s["season"] and (not seen or seen[-1] != s["season"]):
                    seen.append(s["season"])
            notes.append(
                f"{label} 的季節標記順序為 {'→'.join(seen)}（可能是回憶或泛指，需人眼確認）"
            )

        rows.append({
            "chapter": label,
            "seasons": seasons,
            "months": months,
            "ages": ages,
        })

    all_ages = sorted({a["age"] for row in rows for a in row["ages"]})
    report = {
        "chapters": rows,
        "notes": notes,
        "age_inventory": all_ages,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            print(f"── {row['chapter']}")
            for s in row["seasons"]:
                print(f"   季節 [{s['token']}]  {s['context']}")
            for a in row["ages"]:
                print(f"   年齡 [{a['age']}歲]  {a['context']}")
            if row["months"]:
                print(f"   月份 {', '.join(row['months'])}")
        print()
        for n in notes:
            print(f"NOTE\t{n}")
        print(f"TIMELINE\tchapters={len(rows)}\tnotes={len(notes)}\tages={all_ages}")
    print("OK\ttimeline\t(report)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
