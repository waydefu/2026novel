#!/usr/bin/env python3
"""Materialize skill mirrors for every tool that discovers them.

One source of truth: `.agents/skills/<name>/SKILL.md` (the agent-compatible
path used by Codex and the agents.md ecosystem, and discovered by OpenCode).

Discovery paths per tool (official docs):
    OpenCode      .opencode/skills/  .claude/skills/  .agents/skills/
    Claude Code   .claude/skills/
    Codex / agents.md ecosystem   .agents/skills/
    Grok CLI      .grok/skills/  (kept for backwards compatibility; path not
                  officially confirmed, so it stays a generated mirror)

Mirrors are generated, never hand-edited.

**Do not materialize more than one mirror per working tree.** OpenCode discovers
all three paths at once and warns that skill names must be unique across
locations; copying the same nine skills into `.claude/skills/` *and*
`.agents/skills/` would load each skill twice. Pick the mirror for the tool you
are actually running and keep the source in `.agents/skills/` as the canonical
copy.

Usage:
    py -3 tools/sync_skills.py --check                # validate source; check mirrors
    py -3 tools/sync_skills.py --mirror .claude/skills # materialize one mirror
    py -3 tools/sync_skills.py --clean                 # remove all mirrors

Governance rules enforced here (registry: governance/rule-budget.json):
    HB-022  Skill 部署位置必須為標準探索路徑，不得只放在單一工具的私有目錄
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import ROOT  # noqa: E402
from validate_skills import collect_skills, validate_skill  # noqa: E402

SOURCE = ROOT / ".agents" / "skills"
MIRRORS = {
    ".claude/skills": "Claude Code",
    ".opencode/skills": "OpenCode（已由 .agents/skills 覆蓋，通常不需要）",
    ".grok/skills": "Grok CLI（相容鏡像，路徑未經官方確認）",
}


def sync(write: bool, mirror: str = "", clean: bool = False) -> int:
    errors: list[str] = []
    skills = collect_skills([SOURCE])
    if not skills:
        print(f"ERROR\tno source skills under {SOURCE}", file=sys.stderr)
        return 2

    for skill_md in skills:
        for err in validate_skill(skill_md):
            errors.append(f"{skill_md.relative_to(ROOT).as_posix()}: {err}")

    if clean:
        for rel_root in MIRRORS:
            target = ROOT / rel_root
            if target.exists():
                shutil.rmtree(target)
                print(f"REMOVED\t{rel_root}")
        if errors:
            for err in errors:
                print(f"ERROR\tskills\t{err}", file=sys.stderr)
            return 1
        print("OK\tskill-mirror\tcleaned")
        return 0

    if write:
        if mirror not in MIRRORS:
            print(f"ERROR\tunknown mirror {mirror}; choose one of {sorted(MIRRORS)}", file=sys.stderr)
            return 2
        target = ROOT / mirror
        if target.exists():
            shutil.rmtree(target)
        for skill_md in skills:
            dest_dir = target / skill_md.parent.name
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(skill_md, dest_dir / "SKILL.md")
        print(f"WROTE\t{mirror}\t{len(skills)} skills\t({MIRRORS[mirror]})")
    else:
        for rel_root in MIRRORS:
            target = ROOT / rel_root
            if not target.exists():
                continue  # not materialized in this working tree — fine
            for skill_md in skills:
                mirror_file = target / skill_md.parent.name / "SKILL.md"
                if not mirror_file.is_file():
                    errors.append(f"鏡像缺少 {mirror_file.relative_to(ROOT).as_posix()}")
                elif not filecmp.cmp(skill_md, mirror_file, shallow=False):
                    errors.append(f"鏡像與來源不同步：{mirror_file.relative_to(ROOT).as_posix()}")

    if errors:
        for err in errors:
            print(f"ERROR\tskills\t{err}", file=sys.stderr)
        print("ERROR\tskill-mirror：來源不合規格或鏡像不同步", file=sys.stderr)
        return 1
    print(f"OK\tskill-mirror\t{len(skills)} skills validated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="只檢查，不寫入")
    parser.add_argument("--mirror", default="", choices=sorted(MIRRORS), help="為單一工具產生鏡像")
    parser.add_argument("--clean", action="store_true", help="移除所有鏡像")
    args = parser.parse_args()
    return sync(write=bool(args.mirror), mirror=args.mirror, clean=args.clean)


if __name__ == "__main__":
    raise SystemExit(main())
