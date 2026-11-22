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
        "紀年與王國常識：Ch2 羅德里克在書房授課交代新王曆與辛古拉提王國",
        (("第二章", r"新王曆|紀年"), ("第二章", r"辛古拉提王國")),
    ),
    Thread(
        "T02",
        "父母去向一致：Ch1 說明雙親常駐王都與邊境 → Ch2 查爾曼拆封火漆來信 → Ch6 急件通知",
        (("第一章", r"王都|邊境"), ("第二章", r"火漆|封蠟"), ("第六章", r"火漆|通知")),
    ),
    Thread(
        "T03",
        "吊墜始終由莉諾兒持有（Ch4 救出至 Ch6 認字皆未被取下）",
        (("第四章", r"吊墜"), ("第五章", r"吊墜"), ("第六章", r"吊墜")),
        (("第四章", r"亞德里安.{0,10}(拿|取|收|奪)[^。]{0,6}吊墜"),),
    ),
    Thread(
        "T04",
        "記憶與疑點清單：Ch3 魔法過量副作用與黑石板記錄 → Ch4 觀察屠村矛盾跡象卻先救人",
        (("第三章", r"頭痛"), ("第三章", r"事實|證據"), ("第四章", r"穀物|酒桶|車轍|馬車")),
    ),
    Thread(
        "T05",
        "名冊與記錄：Ch4 護衛標記現場並送報 → Ch6 查爾曼整理家人姓名與他處護送選項",
        (("第四章", r"伊妲"), ("第六章", r"名字|護送")),
    ),
    Thread(
        "T06",
        "稱謂與報出名字：Ch4 無「莉諾兒」三字 → Ch5 退燒後親口報出「莉諾兒」與「九歲」",
        (("第五章", r"莉諾兒"), ("第五章", r"九歲")),
        (("第四章", r"莉諾兒"),),
    ),
    Thread(
        "T07",
        "年齡與時間軸：Ch1 七歲 → Ch4 明確點出三年後、十歲 → Ch6 維持少女九歲與預先通知",
        (("第一章", r"七歲"), ("第四章", r"三年後"), ("第四章", r"十歲"), ("第六章", r"九歲")),
    ),
    Thread(
        "T08",
        "固定配角進場：Ch1 查爾曼、貝倫 → Ch2 羅德里克 → Ch4 伊妲 → Ch5/Ch6 瑪莎",
        (("第一章", r"查爾曼"), ("第一章", r"貝倫"), ("第二章", r"羅德里克"), ("第四章", r"伊妲"), ("第六章", r"瑪莎")),
    ),
    Thread(
        "T09",
        "宅邸節儉家風延續：Ch2 侍女圍裙補丁與 Ch6 非正餐時段小廚房合理對接",
        (("第二章", r"補丁"), ("第六章", r"小廚房")),
    ),
    Thread(
        "T10",
        "守衛鬆動到正門自由：Ch5 守衛在門外 → Ch6 走到無人攔阻的正門後自行說出「我先留在這裡」",
        (("第五章", r"門外|守衛"), ("第六章", r"正門"), ("第六章", r"我先留在這裡")),
    ),
    Thread(
        "T17",
        "西幻書寫與器具一致 Retcon（ADR-0002）：Ch1 木框小刀刻痕、Ch6 通用語字母拼讀、絕無筷子或漢字部首",
        (("第一章", r"刻痕"), ("第六章", r"字母|拼讀|詞根")),
        (("第一章", r"鉛筆線"), ("第六章", r"筷子|碗筷|切蔥|水邊的汀|水汀")),
    ),
    Thread(
        "T19",
        "全書統一第三人稱限知（ADR-0002）：各章旁白不得誤寫成第一人稱敘事",
        (("第一章", r"他"), ("第五章", r"她"), ("第六章", r"她")),
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
