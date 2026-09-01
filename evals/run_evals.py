#!/usr/bin/env python3
"""Governance runtime evals. Proves gates, compiler isolation, drift, recovery. Not literary quality."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "evals"))

from check_derived_drift import drift_check  # noqa: E402
from check_revision_gate import (  # noqa: E402
    CANON_SETTINGS,
    GOV11,
    PROSE,
    check_revision,
    classify_file,
    parse_git_z,
    posix,
    unescape_git_quoted,
)
from compile_context import compile_target  # noqa: E402
from prose_checks import (  # noqa: E402
    CHANGELOG,
    DRAFT,
    GOVERNANCE_11,
    LURE_TOKEN,
    classify_path,
    scan_hard_gate,
    scan_pattern_risk,
)
from recovery.drill import run_recovery_drill  # noqa: E402

FIXTURES = ROOT / "evals" / "fixtures"
SANDBOX = FIXTURES / "compiler_sandbox"


def expect(name: str, cond: bool, detail: str, failures: list[str], passed: list[str]) -> None:
    if cond:
        passed.append(name)
    else:
        failures.append(f"{name}: {detail}")


def main() -> int:
    failures: list[str] = []
    passed: list[str] = []

    expect(
        "fail_tbd_word",
        any("TBD" in h.kind for h in scan_hard_gate(FIXTURES / "fail_tbd.md")),
        "word TBD in prose must be red",
        failures,
        passed,
    )
    expect(
        "fail_tbd_bracket",
        any("TBD" in h.kind for h in scan_hard_gate(FIXTURES / "fail_tbd_bracket.md")),
        "[TBD] in prose must be red",
        failures,
        passed,
    )
    expect(
        "fail_pcode_heading",
        any("P-0" in h.kind for h in scan_hard_gate(FIXTURES / "fail_pcode.md")),
        "P-01 heading must be red",
        failures,
        passed,
    )
    expect(
        "fail_pcode_title",
        any("P-0" in h.kind for h in scan_hard_gate(FIXTURES / "fail_pcode_inline_title.md")),
        "chapter title with P-02 must be red",
        failures,
        passed,
    )
    expect(
        "fail_name_adrian",
        any("姓名" in h.kind for h in scan_hard_gate(FIXTURES / "fail_name.md")),
        "Adrian / middle-dot must be red",
        failures,
        passed,
    )
    expect(
        "fail_name_ascii_dot",
        any("姓名" in h.kind for h in scan_hard_gate(FIXTURES / "fail_name_ascii_dot.md")),
        "亞德里安.梵恩 must be red",
        failures,
        passed,
    )
    expect(
        "pass_clean_prose",
        scan_hard_gate(FIXTURES / "pass_clean.md") == [],
        "clean fixture should pass",
        failures,
        passed,
    )
    cleric = FIXTURES / "pass_cleric_and_choice.md"
    cleric_hits = scan_hard_gate(cleric)
    cleric_pat = scan_pattern_risk(cleric)
    expect("pass_pastor_not_hard", cleric_hits == [], f"hard hits {cleric_hits}", failures, passed)
    expect(
        "pass_choice_not_info01",
        not any("INFO-01" in h.kind for h in cleric_pat),
        "「還是／又X又Y」must not be INFO-01",
        failures,
        passed,
    )
    expect(
        "pass_pastor_not_term_hit",
        not any("牧師" in h.text and "醫師" in h.kind for h in cleric_pat),
        "牧師 must not be treated as 醫師 misuse",
        failures,
        passed,
    )
    expect(
        "exempt_governance_tbd",
        classify_path(FIXTURES / "exempt_governance_tbd.md") == "exempt"
        and scan_hard_gate(FIXTURES / "exempt_governance_tbd.md") == [],
        "governance TBD must not hard-fail",
        failures,
        passed,
    )
    expect(
        "exempt_changelog_history",
        scan_hard_gate(FIXTURES / "exempt_changelog_history.md") == [],
        "00A-style history must not hard-fail",
        failures,
        passed,
    )
    expect(
        "exempt_backup_surface",
        scan_hard_gate(FIXTURES / "exempt_backup_lure.md") == [],
        "backup-scope TBD/name must not hard-fail",
        failures,
        passed,
    )
    expect(
        "exempt_live_11",
        classify_path(GOVERNANCE_11) == "governance" and scan_hard_gate(GOVERNANCE_11) == [],
        "live 11 TBD must be out of prose scope",
        failures,
        passed,
    )
    expect(
        "exempt_live_00a",
        classify_path(CHANGELOG) == "exempt" and scan_hard_gate(CHANGELOG) == [],
        "live changelog must be exempt",
        failures,
        passed,
    )
    patterns = scan_pattern_risk(FIXTURES / "pattern_candidates.md")
    expect("pattern_candidates_present", len(patterns) >= 3, f"got {len(patterns)}", failures, passed)
    expect(
        "pattern_not_hard_gate",
        scan_hard_gate(FIXTURES / "pattern_candidates.md") == [],
        "pattern risk must not auto hard-fail",
        failures,
        passed,
    )
    expect(
        "pattern_file_scope",
        classify_path(FIXTURES / "pattern_candidates.md") == "pattern",
        "pattern fixture scope",
        failures,
        passed,
    )

    r1_canon = check_revision(
        {"revision_level": "R1", "canon_change": False, "governance_sync": False},
        [CANON_SETTINGS],
        [],
    )
    expect("r1_edit_canon_red", bool(r1_canon), "R1+01-06 must fail", failures, passed)

    r3_nobak = check_revision(
        {"revision_level": "R3", "canon_change": False, "governance_sync": True},
        [PROSE],
        [],
    )
    expect("r3_without_backup_red", bool(r3_nobak), "R3 without backup_ref must fail", failures, passed)

    r11_only = check_revision(
        {
            "revision_level": "R2",
            "canon_change": False,
            "governance_sync": True,
            "backup_ref": "99_備份/01_正文備份/eval.md",
        },
        [GOV11],
        ["99_備份/01_正文備份/eval.md"],
    )
    expect("derived_11_without_prose_red", bool(r11_only), "11 without prose must fail", failures, passed)

    bak_edit = check_revision(
        {"revision_level": "R1", "canon_change": False, "governance_sync": False},
        ["99_備份/01_正文備份/既有檔.md"],
        [],
    )
    expect("backup_rewritten_red", bool(bak_edit), "modifying existing backup must fail", failures, passed)

    r4_noflag = check_revision(
        {"revision_level": "R4", "canon_change": False, "governance_sync": True, "backup_ref": "99_備份/x.md"},
        [CANON_SETTINGS],
        ["99_備份/x.md"],
    )
    expect("r4_canon_without_flag_red", bool(r4_noflag), "R4 canon_change=false must fail", failures, passed)

    r2_ok = check_revision(
        {
            "revision_level": "R2",
            "target": "chapter-07",
            "canon_change": False,
            "governance_sync": True,
            "backup_ref": "99_備份/01_正文備份/ok.md",
        },
        [PROSE, GOV11],
        ["99_備份/01_正文備份/ok.md"],
    )
    expect("r2_prose_with_backup_green", r2_ok == [], f"{r2_ok}", failures, passed)

    r0_ok = check_revision(
        {"revision_level": "R0", "target": "ops-runtime", "canon_change": False, "governance_sync": False},
        ["tools/prose_checks.py", "AGENTS.md"],
        ["99_備份/00_非現行｜Compiler誘餌｜請勿施工.md"],
    )
    expect("r0_ops_green", r0_ok == [], f"{r0_ok}", failures, passed)

    expect("posix_keeps_dot_github", posix(".github/workflows/governance-ci.yml") == ".github/workflows/governance-ci.yml", posix(".github/workflows/governance-ci.yml"), failures, passed)
    expect("posix_keeps_dot_grok", posix(".grok/skills/novel-draft-mode/SKILL.md") == ".grok/skills/novel-draft-mode/SKILL.md", posix(".grok/skills/novel-draft-mode/SKILL.md"), failures, passed)
    expect("posix_keeps_gitignore", posix(".gitignore") == ".gitignore", posix(".gitignore"), failures, passed)
    expect("posix_strips_dot_slash_only", posix("./tools/prose_checks.py") == "tools/prose_checks.py", posix("./tools/prose_checks.py"), failures, passed)
    expect("classify_dot_github_ops", classify_file(".github/workflows/governance-ci.yml") == "ops", classify_file(".github/workflows/governance-ci.yml"), failures, passed)
    expect("classify_dot_grok_ops", classify_file(".grok/README.md") == "ops", classify_file(".grok/README.md"), failures, passed)
    expect("classify_gitignore_ops", classify_file(".gitignore") == "ops", classify_file(".gitignore"), failures, passed)

    changelog = "00A_設定歷史修改紀錄｜Changelog.md"
    lure = "99_備份/00_非現行｜Compiler誘餌｜請勿施工.md"
    quoted_changelog = '"' + "".join(f"\\{b:03o}" if b >= 128 else chr(b) for b in changelog.encode("utf-8")) + '"'
    quoted_lure = '"' + "".join(f"\\{b:03o}" if b >= 128 else chr(b) for b in lure.encode("utf-8")) + '"'
    expect("unescape_changelog_utf8", unescape_git_quoted(quoted_changelog) == changelog, unescape_git_quoted(quoted_changelog), failures, passed)
    expect("classify_quoted_changelog_ops", classify_file(quoted_changelog) == "ops", classify_file(quoted_changelog), failures, passed)
    expect("classify_quoted_lure_backup", classify_file(quoted_lure) == "backup", classify_file(quoted_lure), failures, passed)

    z_blob = b".github/workflows/governance-ci.yml\0.grok/skills/x.md\0" + changelog.encode("utf-8") + b"\0"
    z_names = parse_git_z(z_blob)
    expect(
        "git_z_mixed_ascii_unicode",
        z_names == [".github/workflows/governance-ci.yml", ".grok/skills/x.md", changelog],
        str(z_names),
        failures,
        passed,
    )

    r0_live_paths = check_revision(
        {"revision_level": "R0", "target": "ops-runtime", "canon_change": False, "governance_sync": False},
        [
            ".github/workflows/governance-ci.yml",
            ".grok/skills/novel-canon-pack/SKILL.md",
            ".gitignore",
            changelog,
            quoted_changelog,
        ],
        [lure],
    )
    expect("r0_dotfiles_and_unicode_green", r0_live_paths == [], f"{r0_live_paths}", failures, passed)

    payload = compile_target(SANDBOX, "P08")
    blob = json.dumps(payload, ensure_ascii=False)
    expect(
        "compiler_ignores_backup_lure",
        LURE_TOKEN not in blob and all(not p.startswith("99_備份") for p in payload["loaded_paths"]),
        f"loaded={payload['loaded_paths']}",
        failures,
        passed,
    )
    expect(
        "compiler_provenance_present",
        any(s["id"].startswith("CANON-04") for s in payload["sources"])
        and any("PLOT-P08" == s["id"] for s in payload["sources"])
        and any(s["id"].startswith("KNOW-") for s in payload["sources"]),
        f"sources={[s['id'] for s in payload['sources']]}",
        failures,
        passed,
    )

    live = compile_target(ROOT, "P08")
    live_blob = json.dumps(live, ensure_ascii=False)
    expect(
        "compiler_live_ignores_repo_lure",
        LURE_TOKEN not in live_blob,
        "live compiler absorbed 99_備份 lure",
        failures,
        passed,
    )
    expect(
        "compiler_live_sources",
        len(live["sources"]) >= 4,
        f"only {len(live['sources'])} sources",
        failures,
        passed,
    )

    fake_draft = "# 第七章｜門一直開著\n\n還在宅邸。\n"
    fake_gov = "[TEXT-FACT Ch8]\nCUT-OFF：現行正文第七章結束。\n"
    fake_outline = "## 09-P08｜留下以後\n"
    drift_bad = drift_check(fake_draft, fake_gov, fake_outline, "莉諾兒")
    expect("drift_future_chapter_red", any("Ch8" in e or "8" in e for e in drift_bad), f"{drift_bad}", failures, passed)

    named_early = "# 第五章｜不能把她留在這裡\n\n莉諾兒站起來。\n# 第六章｜x\n\n"
    drift_name = drift_check(named_early, "CUT-OFF：現行正文第七章結束。\n", "09-P08", "莉諾兒")
    expect("drift_ch5_name_red", any("莉諾兒" in e for e in drift_name), f"{drift_name}", failures, passed)

    ok_rec, rec_detail = run_recovery_drill()
    expect("recovery_drill", ok_rec, rec_detail, failures, passed)

    if not DRAFT.is_file():
        failures.append("live_draft_missing")
    else:
        live_hits = scan_hard_gate(DRAFT)
        expect("live_draft_hard_gate", live_hits == [], str(live_hits), failures, passed)
        live_drift = drift_check(
            DRAFT.read_text(encoding="utf-8"),
            GOVERNANCE_11.read_text(encoding="utf-8"),
            (ROOT / "10_現行創作資料" / "09_序章～第一篇章節大綱｜第二版.md").read_text(encoding="utf-8"),
            (ROOT / "10_現行創作資料" / "01-08_小說設定總表｜角色・關係・劇情資料.md").read_text(encoding="utf-8"),
        )
        expect("live_drift", live_drift == [], str(live_drift), failures, passed)

    total = len(passed) + len(failures)
    if failures:
        print("EVAL FAIL")
        for item in failures:
            print(f"- {item}")
        print(f"passed={len(passed)} failed={len(failures)} total={total}")
        return 1
    print(f"EVAL OK\t{len(passed)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
