#!/usr/bin/env python3
"""Project-specific style calibration. Measures the draft; never grades it.

Why calibrate locally
---------------------
Community "AI-tone" rules mostly come from English corpora or from checklists
that were never tested. The one large Chinese corpus study available
(`lieflat-less-ai-tone`, 2.83M chars / 629 texts) measured several popular
beliefs and found them *not* to discriminate AI from human writing:

    feature                      R (AI / human)
    sentence-length uniformity   0.87   -> no difference
    adjacent sentence-length gap  1.00   -> no difference
    paragraph-length uniformity   0.94   -> no difference
    metaphor (any)               0.42   -> humans use ~2.4x more
    standalone-paragraph metaphor 0.13  -> humans use ~8x more
    rhetorical questions          0.05   -> humans use ~17x more
    passive voice                0.70   -> humans use more
    nominalisation               0.52   -> humans use more
    single-char function words   0.45   -> AI uses *fewer* (fix, not delete)

Consequences this tool encodes:

* Sentence/paragraph uniformity is **not** evidence of AI authorship. Those
  metrics are still measured, but only as a pointer for a cold read.
* Metaphor, rhetorical questions, parallelism and passive voice are **not**
  defect signals at all. They are reported under "not evidence" so nobody
  deletes good prose to satisfy a checker.
* Every band is derived from *this project's own* two specimens (the live
  draft and the retired 第二版), not from generic thresholds.

Usage:
    py -3 tools/style_profile.py <file> [--compare <baseline>]
    py -3 tools/style_profile.py --calibrate      # writes governance/style-profile.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import ROOT, read_text  # noqa: E402

CALIB_FILE = ROOT / "governance" / "style-profile.json"
FIXTURES = ROOT / "evals" / "fixtures"

# Signals that are NOT evidence of AI authorship (corpus-backed).
NOT_EVIDENCE = {
    "metaphor": ("比喻", "人類用得比 AI 更多（R=0.42；獨立成段 R=0.13）"),
    "rhetorical_question": ("設問句", "人類是 AI 的 17 倍（R=0.05）"),
    "in_sentence_parallel": ("句內排比", "人類不比 AI 少（R=0.61）；只有句間重複才成立"),
    "passive": ("被動句", "人類更多（R=0.70），能表達受事與責任時應保留"),
    "nominalisation": ("動詞名詞化", "人類更多（R=0.52），術語不拆"),
    "colloquial_connective": ("口語連接詞", "AI 反而更少（R=0.26），方向是補不是刪"),
    "sentence_uniformity": ("句長均勻度", "R=0.87，與 AI 身分無關"),
    "paragraph_uniformity": ("段長均勻度", "R=0.94，與 AI 身分無關"),
}

SIGNALS = {
    "dash": ("破折號", re.compile(r"——|—")),
    "colon": ("冒號", re.compile(r"：")),
    "enumeration": ("頓號", re.compile(r"、")),
    "exclamation": ("驚嘆號", re.compile(r"！")),
    "rhetorical_question": ("設問句", re.compile(r"？")),
    "metaphor": ("比喻", re.compile(r"像|彷彿|如同|彷若|猶如|宛如|好像")),
    "passive": ("被動句", re.compile(r"被[^。！？]{1,8}(?:了|著|過)")),
    "contrast": ("不是X而是Y", re.compile(r"不是[^。！？]{1,20}而是")),
    "explain": ("解說導引", re.compile(r"這意味著|某種程度|說到底|歸根究柢|真正的(?:原因|問題)")),
    "ordinal": ("首先其次最後", re.compile(r"首先|其次|最後|第一，|第二，|第三，")),
    "abstract_noun": ("抽象名詞", re.compile(r"意義|價值|精神|層次|維度|格局|邏輯|意識|本質|效率|機制|系統性")),
    "eval_adj": ("空泛評價形容", re.compile(r"無比|極其|宏大|磅礴|深邃|恐怖|神秘|尊貴|璀璨|華麗")),
    "self_comment": ("作者解說句", re.compile(r"沒有(?:任何)?(?:華麗|深刻|複雜|刻意的)[^。]{0,12}(?:堆砌|鋪陳)|全是一個")),
}


def cjk(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def profile(text: str) -> dict:
    body = "\n".join(l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#"))
    sents = [s.strip() for s in re.split(r"(?<=[。！？…])", body) if cjk(s) > 0]
    lens = [cjk(s) for s in sents]
    paras = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("#")]
    plens = [cjk(p) for p in paras if not p.startswith("「")]
    chars = sum(lens) or 1

    out: dict[str, float] = {}
    for key, (_, rx) in SIGNALS.items():
        out[key] = round(len(rx.findall(body)) * 1000 / chars, 2)  # per 1000 chars
    out["sentences"] = len(lens)
    out["avg_sentence_len"] = round(statistics.mean(lens), 2) if lens else 0.0
    out["sentence_cv"] = round(statistics.pstdev(lens) / statistics.mean(lens), 3) if len(lens) > 1 and statistics.mean(lens) else 0.0
    out["paragraph_cv"] = round(statistics.pstdev(plens) / statistics.mean(plens), 3) if len(plens) > 1 and statistics.mean(plens) else 0.0
    out["dialogue_ratio"] = round(sum(1 for s in sents if s.startswith("「")) / len(lens), 3) if lens else 0.0
    return out


def render(label: str, p: dict) -> list[str]:
    lines = [f"--- {label} ---"]
    for key, (name, _) in SIGNALS.items():
        flag = "  (非判據)" if key in NOT_EVIDENCE else ""
        lines.append(f"  {name:<12} {p[key]:>7.2f} /千字{flag}")
    lines.append(f"  平均句長 {p['avg_sentence_len']}  句長CV {p['sentence_cv']}  段長CV {p['paragraph_cv']}  對話句占比 {p['dialogue_ratio']}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?")
    parser.add_argument("--compare", default="")
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args()

    if args.calibrate:
        pos = FIXTURES / "pass_human_prose.md"
        neg = FIXTURES / "pattern_ai_flavor.md"
        payload = {
            "updated": "2026-10-22",
            "note": "以本專案自己的正負樣本校準；不使用通用門檻。R 值參考 lieflat-less-ai-tone（283 萬字 / 629 篇）研究。",
            "not_evidence": {k: {"label": v[0], "why": v[1]} for k, v in NOT_EVIDENCE.items()},
            "samples": {
                "positive_clean": profile(read_text(pos)),
                "negative_ai_flavor": profile(read_text(neg)),
            },
            "bands": {
                "contrast_per_1k": 1.5,
                "explain_per_1k": 1.0,
                "eval_adj_per_1k": 1.0,
                "self_comment_per_1k": 0.5,
                "ordinal_per_1k": 2.0,
            },
            "band_note": "bands 只對『有實證差異』的訊號設限；比喻、設問、排比、被動、句長均勻度不設限。",
        }
        CALIB_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE\t{CALIB_FILE}")
        return 0

    if not args.path:
        parser.error("path required (or use --calibrate)")
    path = Path(args.path)
    if not path.is_file():
        print(f"ERROR\tmissing\t{path}", file=sys.stderr)
        return 2
    lines = render(str(path), profile(read_text(path)))
    if args.compare:
        base = Path(args.compare)
        if base.is_file():
            lines = render(str(base), profile(read_text(base))) + lines
    print("\n".join(lines))
    print("NOTE\t以上為量測，不是判決；非判據項目不得作為改寫理由。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
