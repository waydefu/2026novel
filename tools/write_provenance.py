#!/usr/bin/env python3
"""Write a committed, auditable record for one chapter revision (三件套證據).

Why
---
If this project is ever published, platforms increasingly require proof that a
text was not simply pasted from a model: the pre-AI draft, the conversation
log, and the first machine output. A Git repo can supply all three, but only if
the habit exists *while* the work happens.

This tool makes the habit cheap and, importantly, honest:

* every artefact is identified by a SHA-256 digest, so a later edit to any of
  them is detectable;
* a missing artefact is written as `UNVERIFIED`, never silently filled in;
* records are never overwritten — the filename carries a run id, and an
  existing file is an error;
* the pre-edit snapshot is verified against git, so a "backup" that does not
  actually match the pre-edit state is caught.

Output lands in `governance/provenance/` as committed Markdown (unlike
`governance/evidence/*.json`, which CI writes and git ignores).
"""

from __future__ import annotations

import argparse
import hashlib
import json
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
UNVERIFIED = "UNVERIFIED"


def cjk(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def sha256_of(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return UNVERIFIED


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ""


def git_blob_sha(path_rel: str, rev: str) -> str:
    """Blob hash of a file at a revision (git's own object id)."""
    out = git("rev-parse", f"{rev}:{path_rel}")
    return out or UNVERIFIED


def artifact(label: str, path: str | None, note: str = "") -> str:
    if not path:
        return f"| {label} | **{UNVERIFIED}**（未提供） |"
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.is_file():
        return f"| {label} | **{UNVERIFIED}**（找不到 {path}） |"
    rel = p.resolve().relative_to(ROOT).as_posix() if p.resolve().is_relative_to(ROOT) else str(p)
    digest = sha256_of(p)[:16]
    extra = f"｜{note}" if note else ""
    return f"| {label} | `{rel}`｜sha256:{digest}{extra} |"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", required=True, help="章名，例如 第五章｜不能把她留在這裡")
    parser.add_argument("--level", default="R1")
    parser.add_argument("--scope", default="", help="修改範圍")
    parser.add_argument("--backup", default="", help="本次的備份路徑（99_備份/…）")
    parser.add_argument("--agent-log", default="", help="對話過程的檔案路徑或可查證位置")
    parser.add_argument("--first-output", default="", help="AI 首版輸出（正文檔）路徑")
    parser.add_argument("--base", default="", help="比對基準 sha：驗證備份是否等於修改前狀態")
    parser.add_argument("--notes", default="", help="改稿意圖")
    parser.add_argument("--kept", default="", help="保留理由（命中但語意成立者）")
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

    # run id keeps same-day runs from colliding; the file must never be overwritten.
    run_id = f"{now.strftime('%Y-%m-%dT%H%M%S')}-{sha256_text(head + args.chapter + now.isoformat())[:6]}"
    name = re.sub(r"[^\w一-鿿｜・]+", "", args.chapter)[:40] or "chapter"
    out = Path(args.out) if args.out else OUT_DIR / f"{run_id}_{name}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        print(f"ERROR\tprovenance\trecord already exists, refusing to overwrite: {out}", file=sys.stderr)
        return 1

    # Verify the backup really is the pre-edit state.
    backup_check = UNVERIFIED
    if args.backup and args.base:
        rel_backup = args.backup.replace("\\", "/")
        bpath = ROOT / rel_backup
        if bpath.is_file():
            base_blob = git_blob_sha("10_現行創作資料/小說正文第三版.md", args.base)
            backup_blob = subprocess.check_output(
                ["git", "hash-object", str(bpath)], cwd=ROOT, text=True
            ).strip()
            backup_check = "MATCH" if base_blob == backup_blob else "MISMATCH"
        else:
            backup_check = "MISSING"

    lines = [
        f"# 修稿溯源｜{args.chapter}",
        "",
        f"- run id：`{run_id}`",
        f"- 日期：{now.strftime('%Y-%m-%d %H:%M %z')}",
        f"- 分支：{branch}｜commit：{head[:12]}",
        f"- Revision Level：{args.level}",
        f"- 修改範圍：{args.scope or '（未填）'}",
        f"- 備份驗證（對比基準 {args.base or '（未提供）'}）：**{backup_check}**",
        "",
        "## 證據三件套",
        "",
        "| 件 | 位置與雜湊 |",
        "|---|---|",
        artifact("跑 AI 前原稿", args.backup),
        artifact("AI 首版輸出", args.first_output),
        artifact("對話過程紀錄", args.agent_log),
        artifact("最終版本（現行正文）", "10_現行創作資料/小說正文第三版.md"),
        "",
        "缺任何一件時該列標記為 UNVERIFIED；不得事後補填成已完成。",
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
        args.kept or "（逐條列舉；若無則寫「無」）",
        "",
        "## 未驗證項目",
        "",
        args.unverified or "（無）",
        "",
        "## 說明",
        "",
        "- 本紀錄證明修改過程有跡可循，不能單獨證明作品為人類原創。",
        "- CI 綠燈只證明被檢查的那些事成立，不等於文學品質通過（見 `governance/quality-evaluation.md`）。",
        "",
        f"（本次正文 {cjk(text)} 中文字；sha256:{sha256_text(text)[:16]}）",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"WROTE\t{out.relative_to(ROOT).as_posix()}")
    print(f"RUN\t{run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
