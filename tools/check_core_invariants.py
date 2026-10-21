#!/usr/bin/env python3
"""Check that the core invariants survive in every agent-facing rule file.

Why
---
`sync_agent_rules.py` proves the Cursor / Copilot / CLAUDE.md files agree with
`governance/agent-rules-source.md`. It cannot prove that source still agrees
with `AGENTS.md` — otherwise all three tools could happily follow an outdated
rule while staying perfectly "in sync".

So the shared non-negotiables carry a stable marker (`[PLOT-RESET]` etc.) and
this gate requires every listed file to contain every marker.

Governance rules enforced here (registry: governance/rule-budget.json):
    HB-024  核心不變條件必須同時存在於根規則與各工具規則檔
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import ROOT  # noqa: E402

INVARIANT_FILE = ROOT / "governance" / "core-invariants.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not INVARIANT_FILE.is_file():
        print(f"ERROR\tmissing\t{INVARIANT_FILE}", file=sys.stderr)
        return 2
    spec = json.loads(INVARIANT_FILE.read_text(encoding="utf-8"))
    errors: list[str] = []

    for rel in spec.get("files", []):
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"缺少規則檔：{rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for inv in spec.get("invariants", []):
            marker = inv["marker"]
            if marker not in text:
                errors.append(f"{rel} 缺少核心不變條件 {marker}（{inv['statement']}）")

    if args.json:
        print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2))
    else:
        for err in errors:
            print(err, file=sys.stderr)
        print(
            f"INVARIANTS\t{len(spec.get('invariants', []))}\tfiles={len(spec.get('files', []))}\tmissing={len(errors)}"
        )
    if errors:
        print("ERROR\tcore-invariants", file=sys.stderr)
        return 1
    print("OK\tcore-invariants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
