#!/usr/bin/env python3
"""Rule-budget gate: keep the always-loaded context small and honest.

Two jobs (audited 2026-10-22):

1. **Budget** — AGENTS.md must stay under the line / directive ceiling.
2. **No silent deletions** — a rule may not disappear. Every rule id that
   existed in the merge base must still exist, either as an active rule or as
   an explicitly retired entry with a reason. A rule that vanishes from the
   registry is a lost rule, not a relocated one.

Enforcement honesty (HB-019 was registered as "enforced by scan_pattern_risk.py",
but no scanner can prove a human cold-read happened):

    machine-enforced  the tool exists AND cites the rule id in its source
    machine-assisted  the tool surfaces candidates; a human still decides
    manual-review     no tool can check it; it needs a pointer to a checklist

Governance rules enforced here (registry: governance/rule-budget.json):
    HB-014  AGENTS.md 不得超過規則體量上限
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import ROOT  # noqa: E402

BUDGET_FILE = ROOT / "governance" / "rule-budget.json"
AGENTS = ROOT / "AGENTS.md"
MODAL = re.compile(r"(不得|禁止|必須|不可|不能|一律|務必|只允許)")
BULLET = re.compile(r"^\s*[-*]\s+\S")
HEADING = re.compile(r"^#{1,6}\s")
ENFORCEMENT_KINDS = {"machine-enforced", "machine-assisted", "manual-review"}


def budget_config(path: Path = BUDGET_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def measure(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    bullets = sum(1 for l in lines if BULLET.match(l))
    numbered = sum(1 for l in lines if re.match(r"^\s*\d+[.)]\s+\S", l))
    return {
        "path": path.name,
        "lines": len(lines),
        "bullets": bullets,
        "numbered": numbered,
        "directives": bullets + numbered,
        "headings": sum(1 for l in lines if HEADING.match(l)),
        "modal_sentences": sum(1 for l in lines if MODAL.search(l)),
        "chars": len(text),
    }


def _git_show(base: str, rel: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"{base}:{rel}"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None


def check(
    agents: Path = AGENTS,
    budget: dict | None = None,
    base: str = "",
) -> list[str]:
    budget = budget or budget_config()
    errors: list[str] = []

    # 1) budget
    stats = measure(agents)
    limits = budget.get("agents_md", {})
    max_lines = limits.get("max_lines")
    max_modal = limits.get("max_modal_sentences")
    max_directives = limits.get("max_directives")
    if max_lines and stats["lines"] > max_lines:
        errors.append(
            f"RULE-BUDGET: AGENTS.md {stats['lines']} 行 > 上限 {max_lines}"
            "（Anthropic 建議 ≤200 行；規則要下沉到 tools/ 或 governance/）"
        )
    if max_directives and stats["directives"] > max_directives:
        errors.append(
            f"RULE-BUDGET: AGENTS.md 指令條目 {stats['directives']} 條 > 上限 {max_directives}"
            "（Anthropic 觀察：150–200 條後遵循率開始下滑）"
        )
    if max_modal and stats["modal_sentences"] > max_modal:
        errors.append(
            f"RULE-BUDGET: AGENTS.md 強制語句 {stats['modal_sentences']} 句 > 上限 {max_modal}（諮詢性）"
        )

    # 2) required docs
    for doc in budget.get("required_docs", []):
        if not (ROOT / doc).is_file():
            errors.append(f"RULE-BUDGET: 必要文件不存在：{doc}")

    # 3) hoisted rules: pointers exist, enforcement kind is honest
    active_ids: set[str] = set()
    for entry in budget.get("hoisted_rules", []):
        rid = str(entry.get("id", "?"))
        active_ids.add(rid)
        kind = entry.get("enforcement", "machine-assisted")
        if kind not in ENFORCEMENT_KINDS:
            errors.append(f"RULE-BUDGET: {rid} 的 enforcement 類型無效：{kind}")
            continue
        target = entry.get("enforced_by", "")
        if not target:
            errors.append(f"RULE-BUDGET: {rid} 沒有 enforced_by 指針（規則可能遺失）")
            continue
        rel = target.split("#")[0]
        tool_path = ROOT / rel
        if not tool_path.is_file():
            errors.append(f"RULE-BUDGET: {rid} 的 enforced_by 不存在：{rel}")
            continue
        if kind == "machine-enforced":
            # The tool must actually cite the rule, otherwise the claim is false.
            if rid not in tool_path.read_text(encoding="utf-8"):
                errors.append(
                    f"RULE-BUDGET: {rid} 標為 machine-enforced，但 {rel} 沒有引用該規則編號"
                )
        for doc in entry.get("docs", []):
            if not (ROOT / doc).is_file():
                errors.append(f"RULE-BUDGET: {rid} 指向的文件不存在：{doc}")

    # 4) registry diff: no rule may vanish without a retirement record
    if base:
        raw = _git_show(base, BUDGET_FILE.relative_to(ROOT).as_posix())
        if raw:
            try:
                old = json.loads(raw)
            except json.JSONDecodeError:
                old = {}
            old_ids = {str(e.get("id")) for e in old.get("hoisted_rules", [])}
            retired_ids = {str(e.get("id")) for e in budget.get("retired_rules", [])}
            for rid in sorted(old_ids - active_ids):
                if rid in retired_ids:
                    continue
                errors.append(
                    f"RULE-BUDGET: 規則 {rid} 從登記表消失且未列入 retired_rules（規則不得無紀錄消失）"
                )
            for entry in budget.get("retired_rules", []):
                if not entry.get("reason"):
                    errors.append(f"RULE-BUDGET: retired rule {entry.get('id')} 缺少 reason")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--base", default="", help="合併基準 sha：檢查規則是否無紀錄消失")
    args = parser.parse_args()
    stats = measure(AGENTS)
    errors = check(base=args.base)
    if args.json:
        print(json.dumps({"stats": stats, "errors": errors}, ensure_ascii=False, indent=2))
    else:
        print(
            f"RULE-BUDGET\tlines={stats['lines']}\tdirectives={stats['directives']}"
            f"\tmodal={stats['modal_sentences']}\theadings={stats['headings']}"
        )
        for err in errors:
            print(err, file=sys.stderr)
    if errors:
        print("ERROR\trule-budget", file=sys.stderr)
        return 1
    print("OK\trule-budget")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
