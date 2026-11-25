#!/usr/bin/env python3
"""Prose rhythm metrics. Candidates only — rhythm never auto-fails a chapter.

Why this exists
---------------
`scan_pattern_risk.py` looks at words. It cannot see the single failure mode
that survives a clean word list: *rhythm flattening* — every sentence short,
every paragraph one beat, every dialogue line clipped. AGENTS.md §5（WHITE PROSE ＆ ANTI-AI）forbids
"一句一段＋短句連發" as fake tension, and §11（FAIL CODES）STYLE-02 grades it as a pattern,
but no gate can see it.

Calibration
-----------
Thresholds are advisory only. The previous baseline used a different
sentence splitter (including cross-line joins and quote false positives);
its numbers are not comparable with this parser. Keep existing candidate
thresholds unchanged pending a deliberate fresh calibration. A human cold
read, not a metric or a detector, determines prose quality.
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
    longest_short_run_line: int = 0
    longest_short_run_snippet: str = ""
    short_run_clusters: int = 0
    short_paragraph_rate: float = 0.0
    dialogue_sentence_ratio: float = 0.0
    dialogue_avg_len: float = 0.0
    narration_avg_len: float = 0.0


def sentence_records(text: str, start_line: int = 1) -> list[tuple[str, int, bool, int]]:
    """Return (surface text, source line, dialogue-only, scene block).

    Newlines bound measurement units even without terminal punctuation.
    A punctuation run (including …… and adjacent closing quotes) stays whole.
    Quoted speech can contain multiple sentences; mixed narrative/quotes are
    classified conservatively as narration. This is lexical, not semantic.
    """
    records = []
    block = 0
    ending = re.compile(r"[。！？…]+[」』”’）】]*")
    for line_no, raw in enumerate(text.splitlines(), start=start_line):
        line = raw.strip()
        if line.startswith("#") or re.fullmatch(r"[─—-]{2,}", line):
            block += 1
            continue
        if not line:
            continue
        cursor = 0
        depth = 0
        spans = [(m.end()) for m in ending.finditer(line)]
        if not spans or spans[-1] != len(line):
            spans.append(len(line))
        for stop in spans:
            surface = line[cursor:stop].strip()
            cursor = stop
            inside = outside = 0
            for char in surface:
                if char in "「『":
                    depth += 1
                elif char in "」』":
                    depth = max(0, depth - 1)
                elif cjk(char):
                    if depth:
                        inside += 1
                    else:
                        outside += 1
            if inside or outside:
                records.append((surface, line_no, bool(inside and not outside), block))
    return records


def split_sentences(text: str) -> list[str]:
    return [surface for surface, _, _, _ in sentence_records(text)]


def is_dialogue_sent(s: str) -> bool:
    records = sentence_records(s)
    return bool(records) and all(dialogue for _, _, dialogue, _ in records)


def analyze(text: str, thresholds: dict, *, start_line: int = 1) -> tuple[Metrics, list[dict]]:
    records = sentence_records(text, start_line)
    body_lines = {n: line.strip() for n, line in enumerate(text.splitlines(), start=start_line)}
    narration_lines = {line_no for _, line_no, dialogue, _ in records if not dialogue}
    paragraphs = [body_lines[n] for n in sorted(narration_lines)]
    sents = [s for s, _, _, _ in records]
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

    run_sents: list[str] = []
    run_line = 0
    previous_block = None
    runs: list[tuple[int, int, str]] = []

    def flush() -> None:
        if run_sents:
            runs.append((len(run_sents), run_line, " ".join(run_sents[:3])))
            run_sents.clear()

    # 台詞和場景切換都中斷敘述短句串；行號指向來源 Markdown。
    for (s, line_no, dialogue, block), length in zip(records, lens):
        if previous_block is not None and block != previous_block:
            flush()
        previous_block = block
        if dialogue or length > thresholds["short_sentence_max_chars"] + 2:
            flush()
            continue
        if not run_sents:
            run_line = line_no
        run_sents.append(s)
    flush()
    if runs:
        best_run, best_line, best_snip = max(runs, key=lambda x: x[0])
        m.longest_short_run = best_run
        m.longest_short_run_line = best_line
        m.longest_short_run_snippet = best_snip[:50]
    m.short_run_clusters = sum(1 for count, _, _ in runs if count >= 3)

    if paragraphs:
        m.short_paragraph_rate = round(sum(1 for p in paragraphs if cjk(p) <= 30) / len(paragraphs), 4)

    dlg = [length for (_, _, dialogue, _), length in zip(records, lens) if dialogue]
    nar = [length for (_, _, dialogue, _), length in zip(records, lens) if not dialogue]
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
        snip = f"（例：{m.longest_short_run_snippet}）" if m.longest_short_run_snippet else ""
        flag("RHYTHM-04", f"最長連續短句串 {m.longest_short_run} 句（起始行 {m.longest_short_run_line}）：疑似碎句製造張力{snip}", m.longest_short_run)
    if m.short_paragraph_rate > thresholds["short_paragraph_rate_high"]:
        flag("RHYTHM-05", f"短段占比 {m.short_paragraph_rate:.0%} > {thresholds['short_paragraph_rate_high']:.0%}：一句一段風險", m.short_paragraph_rate)
    if m.dialogue_avg_len and m.narration_avg_len and (m.dialogue_avg_len / m.narration_avg_len) < thresholds["dialogue_to_narration_ratio_low"]:
        flag("RHYTHM-06", f"台詞均長 {m.dialogue_avg_len} 相對敘述 {m.narration_avg_len} 過短：台詞可能不成句", (m.dialogue_avg_len, m.narration_avg_len))
    if m.dialogue_avg_len and m.dialogue_avg_len < thresholds["dialogue_avg_len_low"]:
        flag("RHYTHM-07", f"台詞平均只有 {m.dialogue_avg_len} 字：疑似被截斷成單字機", m.dialogue_avg_len)
    return out


def analyze_by_chapter(text: str, thresholds: dict) -> list[dict]:
    rows: list[dict] = []
    heads = list(CHAPTER_HEAD.finditer(text))
    for i, head in enumerate(heads):
        name = head.group(1)
        stop = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        chunk = text[head.end():stop]
        m, cands = analyze(chunk, thresholds, start_line=text.count("\n", 0, head.end()) + 1)
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
        if args.json:
            print(json.dumps({"scope": scope, "exempt": True, "overall": asdict(Metrics()), "candidates": [], "chapters": []}, ensure_ascii=False))
        else:
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
            snip_col = f"\trun_max={met['longest_short_run']}({met['longest_short_run_snippet'][:24]})" if met.get("longest_short_run", 0) >= 6 else ""
            print(f"CHAPTER\t{row['chapter']}\tavg={met['avg_sentence_len']}\tstdev={met['sentence_stdev']}\tshort={met['short_sentence_rate']:.2f}\t{flag}{snip_col}")
    if not args.json:
        print("NOTE\t節奏候選需人工依 AGENTS.md §5／§11 STYLE-02／§13 冷讀判定，工具不自動判錯。")
    return 1 if (args.strict and (cands or any(r["candidates"] for r in chapters))) else 0


if __name__ == "__main__":
    raise SystemExit(main())
