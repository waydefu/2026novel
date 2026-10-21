#!/usr/bin/env python3
"""Validate skills against the Agent Skills specification.

Spec (https://agentskills.io/specification, OpenCode docs):
    * one folder per skill, containing an uppercase `SKILL.md`
    * `name` required, 1–64 chars, `^[a-z0-9]+(-[a-z0-9]+)*$`, and it must
      match the directory name
    * `description` required, 1–1024 chars
    * optional top-level keys: license, compatibility, metadata
    * `metadata` must be a string→string map (an array value is invalid)
    * no other top-level keys — extra keys hard-error when packaging to
      claude.ai, so a loader that is lenient here will still fail later

Governance rules enforced here (registry: governance/rule-budget.json):
    HB-021  Skill 必須符合 Agent Skills 規格且可被目標工具發現
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import ROOT  # noqa: E402

SKILL_ROOTS = {
    "source": ROOT / ".agents" / "skills",
}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict, list[str]]:
    """Minimal YAML frontmatter reader (no third-party deps).

    Supports one level of nesting (the `metadata:` map), scalars and simple
    lists. A list value under `metadata` is reported as a type error, because
    the Agent Skills spec requires metadata to be a string→string map.
    """
    errors: list[str] = []
    if not text.startswith("---"):
        return {}, ["frontmatter 必須是檔案第一行開始的 --- 區塊"]
    end = text.find("\n---", 3)
    if end == -1:
        return {}, ["frontmatter 缺少結束的 ---"]
    block = text[3:end]
    data: dict = {}
    current: str | None = None
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if stripped.startswith("- "):
            if current is None:
                errors.append(f"frontmatter 有孤立的清單項目：{stripped[:40]}")
                continue
            if isinstance(data.get(current), dict) and not data[current]:
                data[current] = []
            if isinstance(data.get(current), list):
                data[current].append(_unquote(stripped[2:].strip()))
            else:
                errors.append(f"frontmatter 清單項目位置錯誤：{stripped[:40]}")
            continue
        if ":" not in stripped:
            errors.append(f"無法解析的 frontmatter 行：{stripped[:40]}")
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if indent == 0:
            if value == "":
                data[key] = {}
                current = key
            else:
                data[key] = _unquote(value)
                current = None
        else:
            if current is None or not isinstance(data.get(current), dict):
                errors.append(f"無法解析的縮排行：{stripped[:40]}")
                continue
            data[current][key] = _unquote(value) if value else []
    return data, errors


def validate_skill(skill_md: Path) -> list[str]:
    errors: list[str] = []
    text = skill_md.read_text(encoding="utf-8")
    meta, parse_errors = parse_frontmatter(text)
    errors += parse_errors
    if not meta:
        return errors or ["frontmatter 為空"]

    name = meta.get("name")
    if not isinstance(name, str) or not name:
        errors.append("缺少 name")
    else:
        if not (1 <= len(name) <= 64):
            errors.append(f"name 長度 {len(name)} 不在 1–64")
        if not NAME_RE.match(name):
            errors.append(f"name 不符合 ^[a-z0-9]+(-[a-z0-9]+)*$：{name}")
        if name != skill_md.parent.name:
            errors.append(f"name 必須與目錄同名：{name} != {skill_md.parent.name}")

    desc = meta.get("description")
    if not isinstance(desc, str) or not desc:
        errors.append("缺少 description")
    elif len(desc) > 1024:
        errors.append(f"description 長度 {len(desc)} 超過 1024")
    elif len(desc) < 20:
        errors.append(f"description 過短（{len(desc)}），無法讓代理判斷何時載入")

    extra = set(meta) - ALLOWED_KEYS
    if extra:
        errors.append(f"不允許的 top-level frontmatter 欄位：{sorted(extra)}（打包到 claude.ai 會硬錯誤）")

    md = meta.get("metadata")
    if md is not None:
        if not isinstance(md, dict):
            errors.append("metadata 必須是字串→字串映射")
        else:
            for key, value in md.items():
                if not isinstance(key, str):
                    errors.append("metadata 的鍵必須是字串")
                if isinstance(value, list):
                    errors.append(
                        f"metadata.{key} 是陣列；Agent Skills 規格要求 metadata 為字串→字串映射"
                        "（請移入 SKILL.md 內文或改成以逗號分隔的字串）"
                    )
                elif not isinstance(value, str):
                    errors.append(f"metadata.{key} 必須是字串，實際為 {type(value).__name__}")
    return errors


def collect_skills(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for skill_md in sorted(root.glob("*/SKILL.md")):
            out.append(skill_md)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT / ".agents" / "skills"))
    args = parser.parse_args()
    root = Path(args.root)
    skills = collect_skills([root])
    if not skills:
        print(f"ERROR\tno skills found under {root}", file=sys.stderr)
        return 2
    failures = 0
    for skill_md in skills:
        errors = validate_skill(skill_md)
        rel = skill_md.relative_to(ROOT).as_posix()
        if errors:
            failures += 1
            print(f"INVALID\t{rel}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"OK\t{rel}")
    print(f"SKILLS\t{len(skills)}\tinvalid={failures}")
    if failures:
        print("ERROR\tskill-spec", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
