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
        "紀年線頭：Ch2 被打斷 → Ch3 羅德里克接住，但不杜撰年份起點",
        (("第二章", r"哪一種紀年|紀年怎麼算|哪一年"), ("第三章", r"紀年|年份從哪裡開始算")),
    ),
    Thread(
        "T02",
        "紀年知情邊界：Ch3 不暗示羅德里克知道轉生，也不再承諾門柱刻字",
        (("第三章", r"少爺問的不是今天幾號|年份從哪裡開始算"),),
        (("第三章", r"這裡的起點跟您那邊不同|門柱"),),
    ),
    Thread(
        "T03",
        "吊墜：由莉諾兒持有（Ch6 的章首鋪陳是這個母題的落點）",
        (("第五章", r"攥著吊墜|抓著吊墜"), ("第六章", r"吊墜"), ("第七章", r"吊墜")),
        (("第五章", r"亞德里安.{0,10}(拿|取|收|奪)[^。]{0,6}吊墜"),),
    ),
    Thread(
        "T04",
        "那幾張地名紙：Ch7 由她收著 → Ch8 仍在她手上",
        (("第七章", r"紙後來一直放在枕頭下面|這些先放著"), ("第八章", r"吊墜|紙")),
    ),
    Thread(
        "T05",
        "記名與記錄：Ch5 護衛刻記號 → Ch7 管家帶著記錄來的",
        (("第五章", r"刻一道|刻下|留下記號"), ("第七章", r"村裡目前能確認的人|記下|整理到這裡")),
    ),
    Thread(
        "T06",
        "稱謂：僕人稱她『莉諾兒小姐』（Ch6 她第一次聽見，之後是日常）",
        (("第六章", r"莉諾兒小姐"),),
    ),
    Thread(
        "T07",
        "年齡：Ch6 報『九歲』；Ch5 亞德里安十歲",
        (("第六章", r"「九歲。」|九歲"), ("第五章", r"亞德里安十歲")),
    ),
    Thread(
        "T08",
        "牧師貝倫的名字：Ch5 起固定，Ch6 她已知名字",
        (("第五章", r"牧師貝倫"), ("第六章", r"貝倫每天來一次|後來聽侍女叫他貝倫"), ("第八章", r"貝倫")),
    ),
    Thread(
        "T09",
        "管家查爾曼：Ch3 起固定",
        (("第三章", r"查爾曼"), ("第五章", r"查爾曼"), ("第七章", r"查爾曼")),
    ),
    Thread(
        "T10",
        "守衛鬆動的節奏：Ch6 仍堵門 → Ch7 守衛消失",
        (("第六章", r"您現在不能出去|守衛"), ("第七章", r"今天沒有人守門了|守衛還在")),
    ),
    Thread(
        "T15",
        "Ch1 的手機：掉在地板上（螢幕朝上），Ch2 不得寫成掉在床邊",
        (("第一章", r"手機掉到地板上"),),
        (("第二章", r"手機掉到床邊"),),
    ),
    Thread(
        "T16",
        "Ch3 裡管家與牧師都像主角早認識的人 → Ch2 必須先讓名字出現",
        (("第二章", r"查爾曼"), ("第二章", r"貝倫牧師")),
    ),
    Thread(
        "T17",
        "書寫系統：Ch8 教的是漢字（汀／聽），Ch2 不得宣稱這個世界「不是中文」",
        (("第八章", r"汀"),),
        (("第二章", r"明明不是中文"),),
    ),
    Thread(
        "T18",
        "「看輕小說」在繁中會被讀成「看不起小說」",
        (("第二章", r"讀過的輕小說"),),
        (("第二章", r"以前看輕小說"),),
    ),
    Thread(
        "T14",
        "廚房：Ch6–Ch8 的廚房是同一個地方（掌勺的婦人）",
        (("第七章", r"廚房|杯子"), ("第八章", r"廚房|掌勺")),
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
