#!/usr/bin/env python3
"""Prose rhythm metrics. Candidates only — rhythm never auto-fails a chapter.

Why this exists
---------------
`scan_pattern_risk.py` looks at words. It cannot see the single failure mode
that survives a clean word list: *rhythm flattening* — every sentence short,
every paragraph one beat, every dialogue line clipped. AGENTS.md §6.3 forbids
"一句一段＋短句連發" as fake tension, and §13 STYLE-02 grades it as a pattern,
but no gate can see it.

Calibration
-----------
Thresholds are deliberately wide bands, not verdicts. They were set from two
anchors measured with this same script:

* positive anchor — live draft (第三版 Ch1–7): avg sentence 12.2, ≤10字 49.5%,
  paragraph ≤30字 81.1%, longest short run 14.
* negative anchor — retired 第二版 (爽文): avg sentence 26.0, ≤10字 19.8%,
  paragraph ≤30字 37.1%.

The live draft already sits at the *short* edge. The bands therefore flag the
"too flat / too clipped" side only, and every hit must be judged by a human
against AGENTS.md §6.3 / §13 STYLE-02 / §14 cold read.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT, ROOT, classify_path, read_text  # noqa: E402

DEFAULT_THRESHOLDS = {
    "short_sentence_max_chars": 10,
    "short_sentence_rate_high": 0.45,
    "avg_sentence_len_low": 11.0,
    "sentence_stdev_low": 7.0,
    "longest_short_run_high": 8,
    "short_paragraph_rate_high": 0.75,
    # 台詞天生比敘述短，ratio 門檻只抓「離譜地短」；真正的截斷用絕對長度抓。
    "dialogue_to_narration_ratio_low": 0.5,
    "dialogue_avg_len_low": 6.0,
}

CHAPTER_HEAD = re.compile(r"^# (第[一二三四五六七八九十百千0-9]+章.*)$", re.MULTILINE)


def cjk(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


@dataclass
class Metrics:
    chars: int = 0
    sentences: int = 0
    paragraphs: int = 0
    avg_sentence_len: float = 0.0
    median_sentence_len: float = 0.0
    sentence_stdev: float = 0.0
    max_sentence_len: int = 0
    short_sentence_rate: float = 0.0
    long_sentence_rate: float = 0.0
    longest_short_run: int = 0
    short_run_clusters: int = 0
    short_paragraph_rate: float = 0.0
    dialogue_sentence_ratio: float = 0.0
    dialogue_avg_len: float = 0.0
    narration_avg_len: float = 0.0


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[。！？…])", text) if cjk(s) > 0]


def analyze(text: str, thresholds: dict) -> tuple[Metrics, list[dict]]:
    body_lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
    body = "\n".join(body_lines)
    paragraphs = [l for l in body_lines if not l.startswith("「")]
    sents = split_sentences(body)
    lens = [cjk(s) for s in sents]
    m = Metrics()
    m.chars = sum(lens)
    m.sentences = len(lens)
    m.paragraphs = len(paragraphs)
    if not lens:
        return m, []
    m.avg_sentence_len = round(statistics.mean(lens), 2)
    m.median_sentence_len = statistics.median(lens)
    m.sentence_stdev = round(statistics.pstdev(lens), 2)
    m.max_sentence_len = max(lens)

    short_max = thresholds["short_sentence_max_chars"]
    m.short_sentence_rate = round(sum(1 for l in lens if l <= short_max) / len(lens), 4)
    m.long_sentence_rate = round(sum(1 for l in lens if l > 30) / len(lens), 4)

    run = 0
    runs: list[int] = []
    # 只算敘述句：台詞天生短，混進來會讓指標對對話密集的章節失真。
    for s, l in zip(sents, lens):
        if s.startswith("「"):
            if run:
                runs.append(run)
            run = 0
            continue
        if l <= thresholds["short_sentence_max_chars"] + 2:
            run += 1
        else:
            if run:
                runs.append(run)
            run = 0
    if run:
        runs.append(run)
    m.longest_short_run = max(runs) if runs else 0
    m.short_run_clusters = sum(1 for r in runs if r >= 3)

    if paragraphs:
        m.short_paragraph_rate = round(sum(1 for p in paragraphs if cjk(p) <= 30) / len(paragraphs), 4)

    dlg = [cjk(s) for s in sents if s.startswith("「")]
    nar = [cjk(s) for s in sents if not s.startswith("「")]
    m.dialogue_sentence_ratio = round(len(dlg) / len(lens), 4)
    m.dialogue_avg_len = round(statistics.mean(dlg), 2) if dlg else 0.0
    m.narration_avg_len = round(statistics.mean(nar), 2) if nar else 0.0
    return m, candidates_for(m, thresholds)


def candidates_for(m: Metrics, thresholds: dict) -> list[dict]:
    out: list[dict] = []

    def flag(code: str, why: str, value) -> None:
        out.append({"code": code, "value": value, "why": why})

    if m.short_sentence_rate > thresholds["short_sentence_rate_high"]:
        flag("RHYTHM-01", f"短句占比 {m.short_sentence_rate:.0%} > {thresholds['short_sentence_rate_high']:.0%}：碎句化風險", m.short_sentence_rate)
    if m.avg_sentence_len < thresholds["avg_sentence_len_low"]:
        flag("RHYTHM-02", f"平均句長 {m.avg_sentence_len} < {thresholds['avg_sentence_len_low']}：句子過度平均", m.avg_sentence_len)
    if m.sentence_stdev < thresholds["sentence_stdev_low"]:
        flag("RHYTHM-03", f"句長標準差 {m.sentence_stdev} < {thresholds['sentence_stdev_low']}：讀感平坦", m.sentence_stdev)
    if m.longest_short_run >= thresholds["longest_short_run_high"]:
        flag("RHYTHM-04", f"最長連續短句串 {m.longest_short_run} 句：疑似碎句製造張力", m.longest_short_run)
    if m.short_paragraph_rate > thresholds["short_paragraph_rate_high"]:
        flag("RHYTHM-05", f"短段占比 {m.short_paragraph_rate:.0%} > {thresholds['short_paragraph_rate_high']:.0%}：一句一段風險", m.short_paragraph_rate)
    if m.dialogue_avg_len and m.narration_avg_len and (m.dialogue_avg_len / m.narration_avg_len) < thresholds["dialogue_to_narration_ratio_low"]:
        flag("RHYTHM-06", f"台詞均長 {m.dialogue_avg_len} 相對敘述 {m.narration_avg_len} 過短：台詞可能不成句", (m.dialogue_avg_len, m.narration_avg_len))
    if m.dialogue_avg_len and m.dialogue_avg_len < thresholds["dialogue_avg_len_low"]:
        flag("RHYTHM-07", f"台詞平均只有 {m.dialogue_avg_len} 字：疑似被截斷成單字機", m.dialogue_avg_len)
    return out


def analyze_by_chapter(text: str, thresholds: dict) -> list[dict]:
    rows: list[dict] = []
    parts = re.split(r"^# (第[一二三四五六七八九十百千0-9]+章.*)$", text, flags=re.MULTILINE)
    for name, chunk in zip(parts[1::2], parts[2::2]):
        m, cands = analyze(chunk, thresholds)
        if not m.sentences:
            continue
        rows.append({"chapter": name, "metrics": asdict(m), "candidates": cands})
    return rows


def load_thresholds(path: Path) -> dict:
    th = dict(DEFAULT_THRESHOLDS)
    if path.is_file():
        try:
            th.update(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    return th


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DRAFT))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--thresholds", default=str(ROOT / "governance" / "rhythm-thresholds.json"))
    parser.add_argument("--strict", action="store_true", help="exit 1 when candidates exist (local use only)")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.is_file():
        print(f"ERROR\tmissing\t{path}", file=sys.stderr)
        return 2
    scope = classify_path(path)
    if scope != "prose":
        print(f"EXEMPT\tscope={scope}\t{path}")
        return 0

    thresholds = load_thresholds(Path(args.thresholds))
    text = read_text(path)
    overall, cands = analyze(text, thresholds)
    chapters = analyze_by_chapter(text, thresholds)

    if args.json:
        print(json.dumps({"overall": asdict(overall), "candidates": cands, "chapters": chapters}, ensure_ascii=False, indent=2))
    else:
        print(f"METRICS\tchars={overall.chars}\tsentences={overall.sentences}\tavg={overall.avg_sentence_len}\tmedian={overall.median_sentence_len}\tstdev={overall.sentence_stdev}")
        print(f"METRICS\tshort_rate={overall.short_sentence_rate:.3f}\tlong_rate={overall.long_sentence_rate:.3f}\tshort_para={overall.short_paragraph_rate:.3f}\tlongest_run={overall.longest_short_run}")
        print(f"METRICS\tdialogue_ratio={overall.dialogue_sentence_ratio:.3f}\tdialogue_avg={overall.dialogue_avg_len}\tnarration_avg={overall.narration_avg_len}")
        for c in cands:
            print(f"CANDIDATE\t{c['code']}\t{c['why']}")
        for row in chapters:
            met = row["metrics"]
            flag = ",".join(c["code"] for c in row["candidates"]) or "-"
            print(f"CHAPTER\t{row['chapter']}\tavg={met['avg_sentence_len']}\tstdev={met['sentence_stdev']}\tshort={met['short_sentence_rate']:.2f}\t{flag}")
    print("NOTE\t節奏候選需人工依 AGENTS.md §6.3／§13 STYLE-02／§14 冷讀判定，工具不自動判錯。")
    return 1 if (args.strict and (cands or any(r["candidates"] for r in chapters))) else 0


if __name__ == "__main__":
    raise SystemExit(main())
