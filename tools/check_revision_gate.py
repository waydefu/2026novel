#!/usr/bin/env python3
"""Enforce R0–R4 against a change manifest and a file list. Does not grade prose.

Governance rules enforced here (registry: governance/rule-budget.json):
    HB-016  修稿必須依 R0–R4 判定，並滿足該級完成定義
"""

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

R0_PREFIXES = (
    ".agents/",
    ".claude/",
    ".opencode/",
    ".grok/",
    "tools/",
    "evals/",
    ".github/",
    ".cursor/",
    "governance/",
)
R0_FILES = {
    "README.md",
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "00A_設定歷史修改紀錄｜Changelog.md",
}


def posix(p: str) -> str:
    """Normalize a git path. Do not lstrip('./') — that eats `.github` / `.grok` / `.gitignore`."""
    p = unescape_git_quoted(p.strip())
    p = p.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p


def unescape_git_quoted(name: str) -> str:
    """Undo `core.quotePath=true` C-quoting (`\"00A_\\350\\250...\"`)."""
    if len(name) >= 2 and name[0] == '"' and name[-1] == '"':
        body = name[1:-1]
        out = bytearray()
        i = 0
        special = {"n": 10, "t": 9, "r": 13, "\\": 92, '"': 34, "a": 7, "b": 8}
        while i < len(body):
            ch = body[i]
            if ch != "\\":
                out.extend(ch.encode("utf-8"))
                i += 1
                continue
            if i + 3 < len(body) and body[i + 1] in "01234567":
                out.append(int(body[i + 1 : i + 4], 8))
                i += 4
                continue
            if i + 1 < len(body):
                out.append(special.get(body[i + 1], ord(body[i + 1])))
                i += 2
                continue
            out.append(92)
            i += 1
        return out.decode("utf-8")
    return name


def parse_git_z(raw: bytes) -> list[str]:
    names: list[str] = []
    for chunk in raw.split(b"\0"):
        if not chunk:
            continue
        names.append(posix(chunk.decode("utf-8")))
    return names


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
    deleted: list[str] | None = None,
    renamed: list[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    level = str(manifest.get("revision_level") or "").upper()
    if level not in {"R0", "R1", "R2", "R3", "R4"}:
        return [f"manifest missing/invalid revision_level: {level!r}"]
    target = str(manifest.get("target") or "").strip()
    if level == "R0":
        if target != "ops-runtime":
            errors.append("R-GATE: R0 requires target: ops-runtime")
    elif not target:
        errors.append(f"R-GATE: {level} requires a non-empty target (narrative PRs use chapter-NN)")
    canon_change = bool(manifest.get("canon_change"))
    governance_sync = bool(manifest.get("governance_sync"))
    backup_ref = manifest.get("backup_ref")
    backup_prune = bool(manifest.get("backup_prune"))
    state_change = str(manifest.get("state_change") or "changed")
    modified_n = [posix(x) for x in modified]
    added_n = [posix(x) for x in added]
    deleted_n = [posix(x) for x in (deleted or [])]
    renamed_n = [posix(x) for x in (renamed or [])]
    changed = modified_n + added_n + deleted_n + renamed_n
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

    # R2+ prose work must move the derived state too, unless the author says the
    # state genuinely did not change (then state_change: none + a reason).
    prose_touched = any(k == "prose" for k in kinds.values())
    derived_touched = any(k == "derived" for k in kinds.values())
    if level in {"R2", "R3", "R4"} and prose_touched and not derived_touched:
        if state_change != "none":
            errors.append(
                "R-GATE: R2+ changed the live draft but did not sync 11 "
                "(set governance_sync: true and update 11, or state_change: none with a reason)"
            )

    rewritten_backups = [rel for rel, k in kinds.items() if k == "backup" and rel in modified_n]
    if rewritten_backups:
        errors.append("R-GATE: 備份區既有檔被修改（只允許新增里程碑快照）: " + ", ".join(rewritten_backups))

    deleted_backups = [rel for rel, k in kinds.items() if k == "backup" and rel in deleted_n]
    if deleted_backups and not backup_prune:
        errors.append(
            "R-GATE: 備份被刪除（里程碑快照不得刪除；改用 backup_prune: true 並在 00A 記錄）: "
            + ", ".join(deleted_backups)
        )

    deleted_canon = [rel for rel, k in kinds.items() if k in {"prose", "canon", "outline", "derived"} and rel in deleted_n]
    if deleted_canon:
        errors.append("R-GATE: 現行檔被刪除（正文／Canon／09／11 不得刪除）: " + ", ".join(deleted_canon))

    renamed_canon = [rel for rel, k in kinds.items() if k in {"prose", "canon", "outline", "derived", "backup"} and rel in renamed_n]
    if renamed_canon:
        errors.append("R-GATE: 現行檔或備份被重新命名（視為刪除＋新增，須走正常流程）: " + ", ".join(renamed_canon))

    if level == "R0":
        for rel, kind in kinds.items():
            if kind == "backup" and rel in added_n:
                continue
            if kind == "ops":
                continue
            errors.append(f"R-GATE: R0 cannot change {rel} ({kind})")

    if level == "R4" and any(k == "canon" for k in kinds.values()) and not canon_change:
        errors.append("R-GATE: R4 Canon edit requires canon_change=true")

    if level in {"R1", "R2"} and any(k == "outline" for k in kinds.values()):
        errors.append(f"R-GATE: {level} cannot change 09; use R3+ for outline")

    return errors


def git_changes(base: str) -> list[tuple[str, str]]:
    """All change types between base and HEAD: (status, path).

    Uses --name-status -z so renames and copies are visible. A gate that only
    looks at M and A can be bypassed by deleting or renaming a file.
    """
    out = subprocess.check_output(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--name-status",
            "--find-renames",
            "--find-copies",
            "-z",
            f"{base}...HEAD",
        ],
        cwd=ROOT,
    )
    fields = [f for f in out.split(b"\0") if f]
    changes: list[tuple[str, str]] = []
    i = 0
    while i < len(fields):
        status = fields[i].decode("utf-8")
        letter = status[0]
        if letter in {"R", "C"}:
            # R100\0old\0new
            if i + 2 >= len(fields):
                break
            old = fields[i + 1].decode("utf-8")
            new = fields[i + 2].decode("utf-8")
            changes.append((letter, posix(old)))
            changes.append((letter, posix(new)))
            i += 3
            continue
        if i + 1 >= len(fields):
            break
        changes.append((letter, posix(fields[i + 1].decode("utf-8"))))
        i += 2
    return changes


def git_names(base: str, diff_filter: str) -> list[str]:
    out = subprocess.check_output(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--name-only",
            "-z",
            f"--diff-filter={diff_filter}",
            f"{base}...HEAD",
        ],
        cwd=ROOT,
    )
    return parse_git_z(out)


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
        changes = git_changes(args.git_base)
        modified = [p for s, p in changes if s == "M"]
        added = [p for s, p in changes if s == "A"]
        deleted = [p for s, p in changes if s == "D"]
        renamed = [p for s, p in changes if s in {"R", "C"}]
    else:
        modified = args.modified or []
        added = args.added or []
        deleted = []
        renamed = []
    errors = check_revision(manifest, modified, added, deleted, renamed)
    if errors:
        for err in errors:
            print(err)
        return 1
    print(f"OK\trevision-gate\t{manifest.get('revision_level')}\t{manifest.get('target')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
