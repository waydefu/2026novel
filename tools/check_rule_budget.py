#!/usr/bin/env python3
"""Rule-budget gate: keep the always-loaded context small and honest.

Why
---
Anthropic's own guidance is that a context file over ~200 lines burns budget
and dilutes compliance; independent summaries put the practical ceiling around
150–200 instructions. `AGENTS.md` is the one file every agent always reads, so
it is the one place where bloat actually costs quality.

This gate therefore does two things:

1. **Budget** — AGENTS.md must stay under a line/instruction ceiling.
2. **No silent deletions** — every rule that was moved out of AGENTS.md must
   appear in `governance/rule-budget.json` with a pointer to where it now lives
   (a tool that enforces it, or a governance doc). Missing pointer = the rule
   was lost, not relocated. That is the "hoist, don't drop" discipline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import ROOT  # noqa: E402

BUDGET_FILE = ROOT / "governance" / "rule-budget.json"
AGENTS = ROOT / "AGENTS.md"
MODAL = re.compile(r"(不得|禁止|必須|不可|不能|一律|務必|只允許)")
BULLET = re.compile(r"^\s*[-*]\s+\S")
HEADING = re.compile(r"^#{1,6}\s")


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


def check(agents: Path = AGENTS, budget: dict | None = None) -> list[str]:
    budget = budget or budget_config()
    errors: list[str] = []
    stats = measure(agents)
    limits = budget.get("agents_md", {})
    max_lines = limits.get("max_lines")
    max_modal = limits.get("max_modal_sentences")
    max_directives = limits.get("max_directives")
    if max_lines and stats["lines"] > max_lines:
        errors.append(
            f"RULE-BUDGET: AGENTS.md {stats['lines']} 行 > 上限 {max_lines}（Anthropic 建議 ≤200 行；規則要下沉到 tools/ 或 governance/）"
        )
    if max_modal and stats["modal_sentences"] > max_modal:
        errors.append(
            f"RULE-BUDGET: AGENTS.md 強制語句 {stats['modal_sentences']} 句 > 上限 {max_modal}（指令密度過高會稀釋遵循）"
        )
    if max_directives and stats["directives"] > max_directives:
        errors.append(
            f"RULE-BUDGET: AGENTS.md 指令條目 {stats['directives']} 條 > 上限 {max_directives}（Anthropic 觀察：150–200 條後遵循率開始下滑）"
        )

    for entry in budget.get("hoisted_rules", []):
        rid = entry.get("id", "?")
        target = entry.get("enforced_by", "")
        if not target:
            errors.append(f"RULE-BUDGET: {rid} 沒有 enforced_by 指針（規則可能遺失）")
            continue
        rel = target.split("#")[0]
        if not (ROOT / rel).is_file():
            errors.append(f"RULE-BUDGET: {rid} 的 enforced_by 不存在：{rel}")
        for doc in entry.get("docs", []):
            if not (ROOT / doc).is_file():
                errors.append(f"RULE-BUDGET: {rid} 指向的文件不存在：{doc}")

    for doc in budget.get("required_docs", []):
        if not (ROOT / doc).is_file():
            errors.append(f"RULE-BUDGET: 必要文件不存在：{doc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    stats = measure(AGENTS)
    errors = check()
    if args.json:
        print(json.dumps({"stats": stats, "errors": errors}, ensure_ascii=False, indent=2))
    else:
        print(
            f"RULE-BUDGET\tlines={stats['lines']}\tbullets={stats['bullets']}\theadings={stats['headings']}\tmodal={stats['modal_sentences']}"
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
