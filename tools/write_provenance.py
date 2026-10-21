#!/usr/bin/env python3
"""Write a committed provenance record for one chapter revision (三件套證據).

Why
---
If this project is ever published, platforms increasingly require proof that a
text was not simply pasted from a model: the pre-AI draft, the conversation
log, and the first machine output. A Git repo can supply all three, but only if
the habit exists *while* the work happens.

This tool makes the habit cheap:

* **原始稿** — `99_備份/01_正文備份/` milestone snapshot (see `novel-backup`).
* **對話過程** — the PR / branch history and the agent session.
* **AI 首版輸出** — this record: what was changed, what the scanners said,
  what was deliberately *not* changed, and what was not verified.

Output lands in `governance/provenance/` as committed Markdown (unlike
`governance/evidence/*.json`, which CI writes and git ignores).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canon_contract import load_contracts, run_contracts  # noqa: E402
from prose_checks import DRAFT, ROOT, read_text, scan_hard_gate, scan_pattern_risk  # noqa: E402
from prose_lexicon import group_counts, scan_lexicon  # noqa: E402
from prose_rhythm import analyze, load_thresholds  # noqa: E402

OUT_DIR = ROOT / "governance" / "provenance"


def cjk(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", required=True, help="章名，例如 第五章｜不能把她留在這裡")
    parser.add_argument("--level", default="R1")
    parser.add_argument("--scope", default="", help="修改範圍")
    parser.add_argument("--backup", default="", help="本次的備份路徑（99_備份/…）")
    parser.add_argument("--agent-log", default="", help="對話過程的位置或摘要")
    parser.add_argument("--notes", default="", help="改稿意圖與保留理由")
    parser.add_argument("--unverified", default="", help="未驗證項目（以逗號分隔）")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    text = read_text(DRAFT)
    hard = scan_hard_gate(DRAFT)
    pattern = scan_pattern_risk(DRAFT)
    lex = scan_lexicon(DRAFT)
    rhythm, rhythm_cands = analyze(text, load_thresholds(ROOT / "governance" / "rhythm-thresholds.json"))
    contracts = run_contracts(text, load_contracts())
    head = git("rev-parse", "HEAD")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    now = datetime.now(timezone.utc).astimezone()

    name = re.sub(r"[^\w一-鿿｜・]+", "", args.chapter)[:40] or "chapter"
    out = Path(args.out) if args.out else OUT_DIR / f"{now.strftime('%Y-%m-%d')}_{name}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# 修稿溯源｜{args.chapter}",
        "",
        f"- 日期：{now.strftime('%Y-%m-%d %H:%M %z')}",
        f"- 分支：{branch}｜commit：{head[:12]}",
        f"- Revision Level：{args.level}",
        f"- 修改範圍：{args.scope or '（未填）'}",
        f"- 備份快照：{args.backup or '（無；R2 以上必須有）'}",
        f"- 對話過程：{args.agent_log or '（PR 與分支紀錄）'}",
        "",
        "## 改稿意圖",
        "",
        args.notes or "（未填）",
        "",
        "## 機械掃描結果（全部為候選，不是判決）",
        "",
        f"- Hard Gate 命中：{len(hard)}",
        f"- Pattern Risk 候選：{len(pattern)}",
        f"- 中文 AI 味詞庫候選：{len(lex)}｜分組：{group_counts(lex) or '無'}",
        f"- 節奏候選：{len(rhythm_cands)}｜平均句長 {rhythm.avg_sentence_len}｜短句率 {rhythm.short_sentence_rate:.0%}",
        f"- Canon 契約違規：{len(contracts)}",
        "",
        "## 事實守恆核對",
        "",
        "- 由 `tools/canon_contract.py` 與 `governance/canon-contracts.json` 檢查；契約只覆蓋已被作者鎖定的既存事實。",
        "- 未列入契約的事實（數字、日期、專名、代詞）仍需人工逐段比對。",
        "",
        "## 保留理由（命中但語意成立者必須列在此處）",
        "",
        "（逐條列舉；若無則寫「無」）",
        "",
        "## 未驗證項目",
        "",
        args.unverified or "（無）",
        "",
        "## 證據三件套對照",
        "",
        "| 件 | 位置 |",
        "|---|---|",
        f"| 跑 AI 前原稿 | {args.backup or '99_備份/01_正文備份/（待補）'} |",
        f"| 對話過程 | {args.agent_log or 'PR ' + head[:12]} |",
        f"| AI 首版輸出 | {out.relative_to(ROOT).as_posix()} |",
        "",
        f"（本次正文 {cjk(text)} 中文字）",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"WROTE\t{out.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
