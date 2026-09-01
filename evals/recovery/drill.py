"""Recovery drill: backup → mutate → FAIL → restore → PASS. Never touches live Canon."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from prose_checks import scan_hard_gate


def run_recovery_drill() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = root / "current.md"
        backup_dir = root / "backup"
        backup_dir.mkdir()
        original = "# 第一章｜測試\n\n亞德里安・梵恩把杯子放下。\n"
        current.write_text(original, encoding="utf-8")
        snapshot = backup_dir / "milestone.md"
        shutil.copyfile(current, snapshot)

        current.write_text(original + "\n明天再處理 TBD。\n", encoding="utf-8")
        mutated = scan_hard_gate(current, force_scope="prose")
        if not mutated:
            return False, "mutation did not trip hard-gate"

        shutil.copyfile(snapshot, current)
        restored = scan_hard_gate(current, force_scope="prose")
        if restored:
            return False, f"restore still dirty: {restored}"
        if current.read_text(encoding="utf-8") != original:
            return False, "restore content mismatch"
        return True, "backup → mutate FAIL → restore PASS"
