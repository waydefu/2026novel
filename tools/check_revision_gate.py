#!/usr/bin/env python3
"""Enforce R0–R4 against a change manifest and a file list. Does not grade prose."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest_loader import load_simple_mapping  # noqa: E402
from prose_checks import ROOT  # noqa: E402

CANON_SETTINGS = "10_現行創作資料/01-08_小說設定總表｜角色・關係・劇情資料.md"
PROSE = "10_現行創作資料/小說正文第三版.md"
OUTLINE = "10_現行創作資料/09_序章～第一篇章節大綱｜第二版.md"
GOV11 = "10_現行創作資料/11_小說工程治理總表｜Knowledge・State・QA・TBD.md"

R0_PREFIXES = (".grok/", "tools/", "evals/", ".github/", "governance/")
R0_FILES = {
    "README.md",
    ".gitignore",
    "AGENTS.md",
    "00A_設定歷史修改紀錄｜Changelog.md",
}


def posix(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def classify_file(rel: str) -> str:
    rel = posix(rel)
    if rel.startswith("99_備份/"):
        return "backup"
    if rel == PROSE:
        return "prose"
    if rel == CANON_SETTINGS:
        return "canon"
    if rel == OUTLINE:
        return "outline"
    if rel == GOV11:
        return "derived"
    if rel.startswith(R0_PREFIXES) or rel in R0_FILES:
        return "ops"
    return "other"


def check_revision(
    manifest: dict,
    modified: list[str],
    added: list[str],
) -> list[str]:
    errors: list[str] = []
    level = str(manifest.get("revision_level") or "").upper()
    if level not in {"R0", "R1", "R2", "R3", "R4"}:
        return [f"manifest missing/invalid revision_level: {level!r}"]
    canon_change = bool(manifest.get("canon_change"))
    governance_sync = bool(manifest.get("governance_sync"))
    backup_ref = manifest.get("backup_ref")
    modified_n = [posix(x) for x in modified]
    added_n = [posix(x) for x in added]
    changed = modified_n + added_n
    kinds = {rel: classify_file(rel) for rel in changed}

    if any(k == "canon" for k in kinds.values()) and not (level == "R4" and canon_change):
        errors.append("R-GATE: 01–06/設定總表 changed without revision_level=R4 and canon_change=true")

    if level == "R1" and any(k in {"canon", "outline", "derived"} for k in kinds.values()):
        errors.append("R-GATE: R1 cannot change Canon, 09, or 11")

    if level in {"R2", "R3", "R4"}:
        if not backup_ref:
            errors.append(f"R-GATE: {level} requires backup_ref")
        else:
            ref = posix(str(backup_ref))
            if not ref.startswith("99_備份/"):
                errors.append("R-GATE: backup_ref must live under 99_備份/")
            elif ref not in added_n:
                disk = ROOT / ref
                if not disk.is_file():
                    errors.append(f"R-GATE: backup_ref missing from added files and not on disk: {ref}")

    if any(k == "derived" for k in kinds.values()) and not any(k == "prose" for k in kinds.values()):
        errors.append("R-GATE: 11 changed without live prose change (derived state cannot drift alone)")

    if any(k == "derived" for k in kinds.values()) and not governance_sync:
        errors.append("R-GATE: 11 changed but governance_sync is not true")

    rewritten_backups = [rel for rel, k in kinds.items() if k == "backup" and rel in modified_n]
    if rewritten_backups:
        errors.append("R-GATE: 備份區既有檔被修改（只允許新增里程碑快照）: " + ", ".join(rewritten_backups))

    if level == "R0":
        for rel, kind in kinds.items():
            if kind == "backup" and rel in added_n:
                continue
            if kind == "ops":
                continue
            if kind == "prose":
                continue
            errors.append(f"R-GATE: R0 cannot change {rel} ({kind})")

    if level == "R4" and any(k == "canon" for k in kinds.values()) and not canon_change:
        errors.append("R-GATE: R4 Canon edit requires canon_change=true")

    if level in {"R1", "R2"} and any(k == "outline" for k in kinds.values()):
        errors.append(f"R-GATE: {level} cannot change 09; use R3+ for outline")

    return errors


def git_names(base: str, diff_filter: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"--diff-filter={diff_filter}", f"{base}...HEAD"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    return [posix(line) for line in out.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(ROOT / "governance" / "change-manifest.yaml"))
    parser.add_argument("--git-base", default="")
    parser.add_argument("--modified", nargs="*", default=None)
    parser.add_argument("--added", nargs="*", default=None)
    args = parser.parse_args()
    path = Path(args.manifest)
    if not path.is_file():
        print(f"ERROR\tmissing manifest\t{path}", file=sys.stderr)
        return 2
    manifest = load_simple_mapping(path)
    if args.git_base:
        modified = git_names(args.git_base, "M")
        added = git_names(args.git_base, "A")
    else:
        modified = args.modified or []
        added = args.added or []
    errors = check_revision(manifest, modified, added)
    if errors:
        for err in errors:
            print(err)
        return 1
    print(f"OK\trevision-gate\t{manifest.get('revision_level')}\t{manifest.get('target')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
