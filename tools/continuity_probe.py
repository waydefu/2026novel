#!/usr/bin/env python3
"""Cross-chapter continuity probe.

Why this exists
---------------
The seven-chapter optimisation pass revised every chapter in isolation. Each
chapter was checked against its own canon and read by a blind reviewer, but
nobody read the book *continuously*, so seams between chapters were invisible.

This probe encodes the cross-chapter threads that the pass touched, so a
regression in one chapter shows up as a red line instead of a reader's
"wait, what?" moment.

Each assertion states a thread, where it must appear, and (optionally) where a
contradiction would be a bug. Output is a report; it never edits prose.

Usage:
    py -3 tools/continuity_probe.py            # report only (exit 1 on failure)
    py -3 tools/continuity_probe.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT, ROOT  # noqa: E402


@dataclass
class Thread:
    tid: str
    title: str
    must: tuple[tuple[str, str], ...]          # (chapter prefix, regex)
    forbidden: tuple[tuple[str, str], ...] = ()  # (chapter prefix, regex)


def chapter_map(text: str) -> dict[str, str]:
    parts = re.split(r"^# (第[一二三四五六七八九十百]+章.*)$", text, flags=re.MULTILINE)
    out: dict[str, str] = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        out[name] = body
    return out


THREADS: list[Thread] = [
    Thread(
        "T01",
        "紀年線頭：Ch2 詢問年份被打斷 → Ch3 羅德里克交代新王曆與辛古拉提王國",
        (("第二章", r"哪一種紀年|哪一年"), ("第三章", r"紀年|新王曆")),
    ),
    Thread(
        "T02",
        "父母去向因果一致：Ch2 大人交代已送信 → Ch3 查爾曼拆火漆家書 → Ch7 急件通知",
        (("第二章", r"王都|北"), ("第三章", r"火漆|信"), ("第七章", r"火漆|通知")),
    ),
    Thread(
        "T03",
        "吊墜始終由莉諾兒持有（Ch5–Ch7 皆未被奪）",
        (("第五章", r"吊墜"), ("第六章", r"吊墜"), ("第七章", r"吊墜")),
        (("第五章", r"亞德里安.{0,10}(拿|取|收|奪)[^。]{0,6}吊墜"),),
    ),
    Thread(
        "T04",
        "過量代價與觀察疑點清單：Ch4 頭痛記憶斷片上鎖 → Ch5 察覺村口糧袋／車轍不合卻先救人",
        (("第四章", r"頭痛"), ("第四章", r"鎖"), ("第五章", r"穀袋|麥袋|木桶|車轍|馬車")),
    ),
    Thread(
        "T05",
        "名冊與記錄：Ch5 護衛刻記號 → Ch7 查爾曼交付石碑記錄與西麓護送路線",
        (("第五章", r"刻一道|記下"), ("第七章", r"名字|護送")),
    ),
    Thread(
        "T06",
        "稱謂與姓名揭露：Ch5 無「莉諾兒」三字 → Ch6 退燒後報出「莉諾兒」與「九歲」",
        (("第六章", r"莉諾兒"), ("第六章", r"九歲")),
        (("第五章", r"莉諾兒"),),
    ),
    Thread(
        "T07",
        "年齡與時間軸：Ch2 七歲 → Ch5 明確寫出三年後、亞德里安十歲 → Ch7 維持九歲",
        (("第二章", r"七歲"), ("第五章", r"三年後"), ("第五章", r"亞德里安十歲"), ("第七章", r"九歲")),
    ),
    Thread(
        "T08",
        "固定配角進場與語氣定位：Ch2 貝倫/查爾曼 → Ch3 羅德里克 → Ch5 伊妲 → Ch6–Ch7 瑪莎",
        (("第二章", r"貝倫"), ("第二章", r"查爾曼"), ("第三章", r"羅德里克"), ("第五章", r"伊妲"), ("第七章", r"瑪莎")),
    ),
    Thread(
        "T09",
        "宅邸節儉家風與餐室禮儀延續：Ch2/3 補丁與僕役用餐規矩 → Ch7 錯開正餐時段的小廚房",
        (("第二章", r"補丁"), ("第三章", r"僕役輪替用餐|僕人輪替用餐"), ("第七章", r"小廚房")),
    ),
    Thread(
        "T10",
        "守衛鬆動到正門自由：Ch6 門外守衛 → Ch7 走到無人阻攔的正門後說「我先留在這裡」",
        (("第六章", r"門外|守衛"), ("第七章", r"正門"), ("第七章", r"我先留在這裡")),
    ),
    Thread(
        "T17",
        "西幻書寫與器具一致（ADR-0002）：Ch2 木柱小刀刻痕、Ch7 通用語字母拼讀、無鉛筆線碗筷或漢字部首",
        (("第二章", r"刻痕"), ("第七章", r"字母|詞根")),
        (("第二章", r"鉛筆線"), ("第七章", r"筷子|碗筷|切蔥|水邊的汀|水汀")),
    ),
    Thread(
        "T18",
        "全書統一第三人稱限知且無『看輕小說』歧義",
        (("第一章", r"讀過的輕小說"),),
        (("第一章", r"看輕小說"), ("第二章", r"看輕小說")),
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--draft", default=str(DRAFT))
    args = parser.parse_args()

    text = Path(args.draft).read_text(encoding="utf-8")
    chapters = chapter_map(text)

    def body_for(prefix: str) -> str:
        for name, body in chapters.items():
            if name.startswith(prefix):
                return body
        return ""

    failures: list[str] = []
    checked = 0
    skipped = 0
    for th in THREADS:
        for prefix, pattern in th.must:
            body = body_for(prefix)
            if not body:
                # The chapter is not written yet; chapters are added one at a time.
                # Skipping is correct — the drift gate covers unsynchronised state.
                skipped += 1
                continue
            checked += 1
            if not re.search(pattern, body):
                failures.append(f"{th.tid}　{prefix} 缺少預期內容 /{pattern}/　（{th.title}）")
        for prefix, pattern in th.forbidden:
            body = body_for(prefix)
            if not body:
                skipped += 1
                continue
            checked += 1
            if re.search(pattern, body):
                failures.append(f"{th.tid}　{prefix} 出現禁止內容 /{pattern}/　（{th.title}）")

    report = {
        "threads": len(THREADS),
        "assertions": checked,
        "skipped_not_written_yet": skipped,
        "failures": failures,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for f in failures:
            print(f"FAIL\t{f}")
        print(f"CONTINUITY\tthreads={len(THREADS)}\tassertions={checked}\tskipped={skipped}\tfailures={len(failures)}")
    if failures:
        print("ERROR\tcontinuity", file=sys.stderr)
        return 1
    print("OK\tcontinuity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
