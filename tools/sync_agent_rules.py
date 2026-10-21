#!/usr/bin/env python3
"""Generate tool-specific agent rule files from one source. No hand-maintained copies.

Every agent tool wants its own rules file (Cursor `.mdc`, Copilot instructions,
`CLAUDE.md`). Maintaining them by hand means they rot and disagree. This
generator keeps `governance/agent-rules-source.md` as the single source and
renders the rest, so drift is impossible by construction and `--check` proves it.

Usage:
    py -3 tools/sync_agent_rules.py          # write
    py -3 tools/sync_agent_rules.py --check  # fail if generated files are stale
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import ROOT  # noqa: E402

SOURCE = ROOT / "governance" / "agent-rules-source.md"
TARGETS = {
    ".cursor/rules/novel-project.mdc": "cursor",
    ".github/copilot-instructions.md": "copilot",
    "CLAUDE.md": "claude",
}
BANNER = "<!-- generated from governance/agent-rules-source.md by tools/sync_agent_rules.py — do not edit by hand -->"


def parse_source(text: str) -> tuple[dict[str, str], str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, flags=re.S)
    if not m:
        raise ValueError("source must start with YAML frontmatter")
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, m.group(2).strip() + "\n"


def render(kind: str, meta: dict[str, str], body: str) -> str:
    desc = meta.get("description", "")
    if kind == "cursor":
        return (
            "---\n"
            f"description: {desc}\n"
            "alwaysApply: true\n"
            "---\n\n"
            f"{BANNER}\n\n"
            f"{body}"
        )
    if kind == "copilot":
        return f"{BANNER}\n\n{body}"
    return f"{BANNER}\n\n{body}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not SOURCE.is_file():
        print(f"ERROR\tmissing source\t{SOURCE}", file=sys.stderr)
        return 2
    meta, body = parse_source(SOURCE.read_text(encoding="utf-8"))

    stale: list[str] = []
    for rel, kind in TARGETS.items():
        target = ROOT / rel
        expected = render(kind, meta, body)
        if args.check:
            current = target.read_text(encoding="utf-8") if target.is_file() else ""
            if current != expected:
                stale.append(rel)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8")
            print(f"WROTE\t{rel}")
    if args.check:
        if stale:
            for rel in stale:
                print(f"RULE-SYNC\tstale\t{rel}", file=sys.stderr)
            print("ERROR\trule-sync：產物與來源不同步，請跑 tools/sync_agent_rules.py", file=sys.stderr)
            return 1
        print(f"OK\trule-sync\t{len(TARGETS)} targets in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
