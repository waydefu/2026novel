#!/usr/bin/env python3
"""Governance runtime evals. Proves gates, compiler isolation, drift, recovery. Not literary quality."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "evals"))

from check_derived_drift import drift_check  # noqa: E402
from manifest_loader import load_simple_mapping  # noqa: E402
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
from canon_contract import check_immutability, load_contracts, run_contracts, validate_schema  # noqa: E402
from check_rule_budget import check as rule_budget_check  # noqa: E402
from compile_context import compile_target, extract_style_anchors, scene_fields, extract_voice_for  # noqa: E402
from prose_lexicon import lexicon_hash, scan_lexicon  # noqa: E402
from prose_rhythm import analyze  # noqa: E402
from style_profile import NOT_EVIDENCE  # noqa: E402
from sync_google_doc import ChapterPayload, parse_chapters, push_webhook, push_gdocs_cli  # noqa: E402
from sync_agent_rules import SOURCE as RULES_SOURCE  # noqa: E402
from sync_agent_rules import TARGETS as RULE_TARGETS  # noqa: E402
from sync_agent_rules import parse_source, render  # noqa: E402
from validate_skills import collect_skills, validate_skill  # noqa: E402
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
        "fail_simplified_char",
        any("FONT-01" in h.kind for h in scan_hard_gate(FIXTURES / "fail_simplified.md")),
        "simplified characters in the prose must be red",
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

    r1_prose = check_revision(
        {"revision_level": "R1", "target": "chapter-08", "canon_change": False, "governance_sync": False},
        [PROSE],
        [],
    )
    expect("r1_prose_green", r1_prose == [], f"{r1_prose}", failures, passed)

    r3_nobak = check_revision(
        {"revision_level": "R3", "canon_change": False, "governance_sync": True},
        [PROSE],
        [],
    )
    expect("r3_without_backup_red", bool(r3_nobak), "R3 without backup_ref must fail", failures, passed)

    r3_prose = check_revision(
        {
            "revision_level": "R3",
            "target": "chapter-08",
            "canon_change": False,
            "governance_sync": True,
            "backup_ref": "99_備份/01_正文備份/r3.md",
        },
        [PROSE, GOV11],
        ["99_備份/01_正文備份/r3.md"],
    )
    expect("r3_prose_with_backup_green", r3_prose == [], f"{r3_prose}", failures, passed)

    r3_prose_no_derived = check_revision(
        {
            "revision_level": "R3",
            "target": "chapter-08",
            "canon_change": False,
            "governance_sync": False,
            "backup_ref": "99_備份/01_正文備份/r3.md",
        },
        [PROSE],
        ["99_備份/01_正文備份/r3.md"],
    )
    expect(
        "r3_prose_without_derived_red",
        bool(r3_prose_no_derived),
        "R3 changed the draft but did not sync 11 — must fail",
        failures,
        passed,
    )

    r2_state_none = check_revision(
        {
            "revision_level": "R2",
            "target": "chapter-08",
            "canon_change": False,
            "governance_sync": False,
            "state_change": "none",
            "state_change_reason": "測試：僅行文修訂，既定狀態不變",
            "backup_ref": "99_備份/01_正文備份/r2.md",
        },
        [PROSE],
        ["99_備份/01_正文備份/r2.md"],
    )
    expect(
        "r2_state_change_none_green",
        r2_state_none == [],
        f"explicit state_change: none must be allowed — {r2_state_none}",
        failures,
        passed,
    )

    # The same escape hatch, but through the real manifest loader: the eval
    # above builds the manifest as a dict, so the loader's own handling of
    # `state_change: none` was never exercised. It used to map the string
    # "none" to YAML null, which turned this into a failure in the real path.
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        loader_case = tmp_path / "manifest_state_none.yaml"
        loader_case.write_text(
            "revision_level: R2\n"
            "target: chapter-08\n"
            "canon_change: false\n"
            "governance_sync: false\n"
            "state_change: none\n"
            "state_change_reason: 僅行文修訂\n"
            "backup_ref: 99_備份/01_正文備份/r2.md\n",
            encoding="utf-8",
        )
        loader_state_none = check_revision(
            load_simple_mapping(loader_case),
            [PROSE],
            ["99_備份/01_正文備份/r2.md"],
        )
        expect(
            "r2_state_change_none_via_loader_green",
            loader_state_none == [],
            f"state_change: none must survive the manifest loader — {loader_state_none}",
            failures,
            passed,
        )

        loader_missing = tmp_path / "manifest_state_absent.yaml"
        loader_missing.write_text(
            "revision_level: R2\n"
            "target: chapter-08\n"
            "canon_change: false\n"
            "governance_sync: false\n"
            "backup_ref: 99_備份/01_正文備份/r2.md\n",
            encoding="utf-8",
        )
        loader_absent_state = check_revision(
            load_simple_mapping(loader_missing),
            [PROSE],
            ["99_備份/01_正文備份/r2.md"],
        )
        expect(
            "r2_state_change_absent_red",
            bool(loader_absent_state),
            "a manifest without state_change must not be read as 'none' — "
            f"{loader_absent_state}",
            failures,
            passed,
        )

    deleted_prose = check_revision(
        {"revision_level": "R1", "target": "chapter-07", "canon_change": False, "governance_sync": False},
        [],
        [],
        deleted=[PROSE],
    )
    expect("deleted_prose_red", bool(deleted_prose), "deleting the live draft must fail", failures, passed)

    deleted_backup = check_revision(
        {"revision_level": "R1", "target": "chapter-07", "canon_change": False, "governance_sync": False},
        [],
        [],
        deleted=["99_備份/01_正文備份/existing.md"],
    )
    expect("deleted_backup_red", bool(deleted_backup), "deleting a backup must fail without backup_prune", failures, passed)

    deleted_backup_pruned = check_revision(
        {
            "revision_level": "R1",
            "target": "chapter-07",
            "canon_change": False,
            "governance_sync": False,
            "backup_prune": True,
        },
        [],
        [],
        deleted=["99_備份/01_正文備份/existing.md"],
    )
    expect(
        "deleted_backup_prune_green",
        deleted_backup_pruned == [],
        f"explicit backup_prune must be allowed — {deleted_backup_pruned}",
        failures,
        passed,
    )

    renamed_backup = check_revision(
        {"revision_level": "R1", "target": "chapter-07", "canon_change": False, "governance_sync": False},
        [],
        [],
        renamed=["99_備份/01_正文備份/existing.md"],
    )
    expect("renamed_backup_red", bool(renamed_backup), "renaming a backup must fail", failures, passed)

    # A byte-identical backup snapshot of a modified live file must NOT be read as
    # a rename of the live file (git's --find-renames used to pair them).
    copy_into_backup = check_revision(
        {
            "revision_level": "R3",
            "target": "chapter-08",
            "canon_change": False,
            "governance_sync": True,
            "state_change": "none",
            "state_change_reason": "測試：僅行文修訂，既定狀態不變",
            "backup_ref": "99_備份/01_正文備份/snapshot.md",
        },
        [PROSE],
        ["99_備份/01_正文備份/snapshot.md"],
    )
    expect(
        "backup_copy_not_rename_green",
        copy_into_backup == [],
        f"adding a backup snapshot must not look like renaming the draft — {copy_into_backup}",
        failures,
        passed,
    )

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

    r4_canon = check_revision(
        {"revision_level": "R4", "target": "chapter-08", "canon_change": True, "governance_sync": True, "backup_ref": "99_備份/01_正文備份/r4.md"},
        [CANON_SETTINGS],
        ["99_備份/01_正文備份/r4.md"],
    )
    expect("r4_canon_with_flag_green", r4_canon == [], f"{r4_canon}", failures, passed)

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

    r0_prose = check_revision(
        {"revision_level": "R0", "target": "ops-runtime", "canon_change": False, "governance_sync": False},
        [PROSE],
        [],
    )
    expect("r0_prose_red", bool(r0_prose), "R0+live prose must fail", failures, passed)

    r0_target = check_revision(
        {"revision_level": "R0", "target": "chapter-08", "canon_change": False, "governance_sync": False},
        ["tools/prose_checks.py"],
        [],
    )
    expect("r0_wrong_target_red", bool(r0_target), "R0 with non-ops target must fail", failures, passed)

    r1_no_target = check_revision(
        {"revision_level": "R1", "canon_change": False, "governance_sync": False},
        [PROSE],
        [],
    )
    expect("r1_empty_target_red", bool(r1_no_target), "R1 without target must fail", failures, passed)

    expect("posix_keeps_dot_github", posix(".github/workflows/governance-ci.yml") == ".github/workflows/governance-ci.yml", posix(".github/workflows/governance-ci.yml"), failures, passed)
    expect("posix_keeps_dot_agents", posix(".agents/skills/novel-draft-mode/SKILL.md") == ".agents/skills/novel-draft-mode/SKILL.md", posix(".agents/skills/novel-draft-mode/SKILL.md"), failures, passed)
    expect("posix_keeps_dot_grok", posix(".grok/skills/novel-draft-mode/SKILL.md") == ".grok/skills/novel-draft-mode/SKILL.md", posix(".grok/skills/novel-draft-mode/SKILL.md"), failures, passed)
    expect("classify_dot_grok_ops", classify_file(".grok/README.md") == "ops", classify_file(".grok/README.md"), failures, passed)
    expect("classify_dot_agents_ops", classify_file(".agents/skills/x/SKILL.md") == "ops", classify_file(".agents/skills/x/SKILL.md"), failures, passed)
    expect("classify_dot_claude_ops", classify_file(".claude/skills/x/SKILL.md") == "ops", classify_file(".claude/skills/x/SKILL.md"), failures, passed)
    expect("classify_dot_opencode_ops", classify_file(".opencode/skills/x/SKILL.md") == "ops", classify_file(".opencode/skills/x/SKILL.md"), failures, passed)
    expect("posix_keeps_gitignore", posix(".gitignore") == ".gitignore", posix(".gitignore"), failures, passed)
    expect("posix_strips_dot_slash_only", posix("./tools/prose_checks.py") == "tools/prose_checks.py", posix("./tools/prose_checks.py"), failures, passed)
    expect("classify_dot_github_ops", classify_file(".github/workflows/governance-ci.yml") == "ops", classify_file(".github/workflows/governance-ci.yml"), failures, passed)
    expect("classify_gitignore_ops", classify_file(".gitignore") == "ops", classify_file(".gitignore"), failures, passed)
    expect("classify_cursor_ops", classify_file(".cursor/environment.json") == "ops", classify_file(".cursor/environment.json"), failures, passed)

    changelog = "00A_設定歷史修改紀錄｜Changelog.md"
    lure = "99_備份/00_非現行｜Compiler誘餌｜請勿施工.md"
    quoted_changelog = '"' + "".join(f"\\{b:03o}" if b >= 128 else chr(b) for b in changelog.encode("utf-8")) + '"'
    quoted_lure = '"' + "".join(f"\\{b:03o}" if b >= 128 else chr(b) for b in lure.encode("utf-8")) + '"'
    expect("unescape_changelog_utf8", unescape_git_quoted(quoted_changelog) == changelog, unescape_git_quoted(quoted_changelog), failures, passed)
    expect("classify_quoted_changelog_ops", classify_file(quoted_changelog) == "ops", classify_file(quoted_changelog), failures, passed)
    expect("classify_quoted_lure_backup", classify_file(quoted_lure) == "backup", classify_file(quoted_lure), failures, passed)

    z_blob = b".github/workflows/governance-ci.yml\0.agents/skills/x.md\0" + changelog.encode("utf-8") + b"\0"
    z_names = parse_git_z(z_blob)
    expect(
        "git_z_mixed_ascii_unicode",
        z_names == [".github/workflows/governance-ci.yml", ".agents/skills/x.md", changelog],
        str(z_names),
        failures,
        passed,
    )

    r0_live_paths = check_revision(
        {"revision_level": "R0", "target": "ops-runtime", "canon_change": False, "governance_sync": False},
        [
            ".github/workflows/governance-ci.yml",
            ".agents/skills/novel-canon-pack/SKILL.md",
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

    # --- governance evolution: contracts, lexicon, rhythm, budget, rule sync ---
    contracts = load_contracts()
    expect(
        "contracts_loaded",
        len(contracts.get("contracts", [])) >= 8,
        f"only {len(contracts.get('contracts', []))} contracts",
        failures,
        passed,
    )
    contract_bad = run_contracts(
        (FIXTURES / "fail_contract_violation.md").read_text(encoding="utf-8"), contracts
    )
    expect(
        "contract_violation_red",
        len(contract_bad) >= 1,
        f"violating fixture must break a contract, got {contract_bad}",
        failures,
        passed,
    )
    bad_scope = {
        "contracts": [
            {
                "id": "CC-BAD-SCOPE",
                "status": "active",
                "title": "scope 指向不存在的章節",
                "scope": {"chapters": ["第九十九章｜不存在"]},
                "forbid": ["奧斯汀"],
                "require": [],
            }
        ]
    }
    scope_hits = run_contracts((FIXTURES / "pass_clean.md").read_text(encoding="utf-8"), bad_scope)
    expect(
        "contract_bad_scope_red",
        any(h.kind == "scope" for h in scope_hits),
        f"missing chapter in scope must be an error, got {scope_hits}",
        failures,
        passed,
    )

    # --json must emit valid JSON *and* exit non-zero when violations exist.
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "canon_contract.py"), str(FIXTURES / "fail_contract_violation.md"), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    json_ok = False
    try:
        payload = json.loads(proc.stdout)
        json_ok = isinstance(payload.get("violations"), list) and payload.get("count", 0) > 0
    except json.JSONDecodeError:
        json_ok = False
    expect("contract_json_valid", json_ok, f"--json did not emit valid JSON: out={proc.stdout[:200]!r} err={proc.stderr[:300]!r}", failures, passed)
    expect("contract_json_exit_nonzero", proc.returncode != 0, f"exit code was {proc.returncode}", failures, passed)

    # Skills must satisfy the Agent Skills spec (name/dir match, allowed keys,
    # metadata as a string→string map).
    skills = collect_skills([ROOT / ".agents" / "skills"])
    expect("skills_present", len(skills) >= 9, f"only {len(skills)} skills", failures, passed)
    skill_errors: list[str] = []
    for skill_md in skills:
        skill_errors += [f"{skill_md.name}: {e}" for e in validate_skill(skill_md)]
    expect("skills_spec_valid", not skill_errors, str(skill_errors), failures, passed)

    mirror_proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "sync_skills.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    expect("skill_mirror_green", mirror_proc.returncode == 0, mirror_proc.stderr[:300], failures, passed)

    invariant_proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_core_invariants.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    expect(
        "core_invariants_green",
        invariant_proc.returncode == 0,
        invariant_proc.stderr[:300],
        failures,
        passed,
    )

    if DRAFT.is_file():
        live_contract = run_contracts(DRAFT.read_text(encoding="utf-8"), contracts)
        expect("contract_live_green", live_contract == [], str(live_contract), failures, passed)

    lock_file = ROOT / "governance" / "lexicon.lock"
    expect(
        "lexicon_lock_matches",
        lock_file.is_file() and lock_file.read_text(encoding="utf-8").strip() == lexicon_hash(),
        "lexicon hash drifted from governance/lexicon.lock",
        failures,
        passed,
    )
    neg_hits = scan_lexicon(FIXTURES / "pattern_ai_flavor.md")
    neg_groups = {h.group for h in neg_hits}
    expect(
        "lexicon_negative_detects",
        len(neg_groups) >= 3,
        f"AI-flavor fixture only hit {len(neg_groups)} groups",
        failures,
        passed,
    )
    pos_hits = scan_lexicon(FIXTURES / "pass_human_prose.md")
    expect(
        "lexicon_false_positive_control",
        len(pos_hits) <= 2,
        f"clean fixture produced {len(pos_hits)} candidates: {[h.group for h in pos_hits]}",
        failures,
        passed,
    )
    if DRAFT.is_file():
        live_lex = scan_lexicon(DRAFT)
        expect(
            "lexicon_live_clean",
            len(live_lex) <= 3,
            f"live draft produced {len(live_lex)} candidates: {[h.group for h in live_lex]}",
            failures,
        passed,
        )

    flat_metrics, flat_cands = analyze(
        (FIXTURES / "pattern_flat_rhythm.md").read_text(encoding="utf-8"),
        {"short_sentence_max_chars": 10, "short_sentence_rate_high": 0.45, "avg_sentence_len_low": 11.0,
         "sentence_stdev_low": 7.0, "longest_short_run_high": 8, "short_paragraph_rate_high": 0.75,
         "dialogue_to_narration_ratio_low": 0.5, "dialogue_avg_len_low": 6.0},
    )
    expect(
        "rhythm_flat_detected",
        len(flat_cands) >= 1,
        f"flat fixture produced no rhythm candidate: {flat_metrics}",
        failures,
        passed,
    )

    expect(
        "not_evidence_present",
        {"metaphor", "rhetorical_question", "sentence_uniformity"} <= set(NOT_EVIDENCE),
        "corpus-backed non-signals missing",
        failures,
        passed,
    )

    budget_errors = rule_budget_check()
    expect("rule_budget_green", budget_errors == [], str(budget_errors), failures, passed)

    if RULES_SOURCE.is_file():
        meta, body = parse_source(RULES_SOURCE.read_text(encoding="utf-8"))
        stale = []
        for rel, kind in RULE_TARGETS.items():
            target = ROOT / rel
            current = target.read_text(encoding="utf-8") if target.is_file() else ""
            if current != render(kind, meta, body):
                stale.append(rel)
        expect("rule_sync_green", not stale, f"stale: {stale}", failures, passed)
    else:
        expect("rule_sync_source_present", False, "governance/agent-rules-source.md missing", failures, passed)

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

    from prose_checks import chapter_number  # noqa: E402

    expect(
        "chapter_number_over_20",
        chapter_number("二十") == 20 and chapter_number("二十五") == 25 and chapter_number("一百零八") == 108,
        f"got 20={chapter_number('二十')}, 25={chapter_number('二十五')}, 108={chapter_number('一百零八')}",
        failures,
        passed,
    )

    a1_payload = compile_target(ROOT, "A1-01")
    expect(
        "compiler_supports_act1_targets",
        a1_payload["target"] == "A1-01" and any(s["id"] == "PLOT-A1-01" for s in a1_payload["sources"]),
        f"target={a1_payload.get('target')} sources={[s['id'] for s in a1_payload.get('sources', [])]}",
        failures,
        passed,
    )
    expect(
        "compiler_loads_real_voice_fingerprint",
        "ATTENTION" in a1_payload["capsule"].get("VOICE", "") and any(s["id"].startswith("VOICE-") for s in a1_payload["sources"]),
        f"VOICE={a1_payload['capsule'].get('VOICE', '')[:120]!r}",
        failures,
        passed,
    )

    inv_hits = scan_hard_gate(FIXTURES / "pass_clean.md", text="這是一段帶有\u200b零寬空白的正文。\n", force_scope="prose")
    expect(
        "fail_invisible_zero_width_char",
        any("FORMAT-01" in h.kind and "U+200B" in h.kind for h in inv_hits),
        f"zero-width char must fail hard gate, got {inv_hits}",
        failures,
        passed,
    )

    r0_derived_header = check_revision(
        {"revision_level": "R0", "target": "ops-runtime", "canon_change": False, "governance_sync": True, "state_change": "none", "state_change_reason": "僅標頭同步"},
        [GOV11],
        [],
    )
    expect(
        "r0_derived_header_sync_green",
        r0_derived_header == [],
        f"R0 header/TBD sync on 11 with governance_sync=true & state_change=none must pass: {r0_derived_header}",
        failures,
        passed,
    )

    r0_derived_unflagged = check_revision(
        {"revision_level": "R0", "target": "ops-runtime", "canon_change": False, "governance_sync": False},
        [GOV11],
        [],
    )
    expect(
        "r0_derived_without_flags_red",
        bool(r0_derived_unflagged),
        "R0 touching 11 without governance_sync=true & state_change=none must fail",
        failures,
        passed,
    )

    routing_doc = (ROOT / "governance" / "skill-routing.md").read_text(encoding="utf-8")
    all_skills_routed = all(f"`{s.parent.name}`" in routing_doc for s in skills)
    expect(
        "all_skills_in_routing_table",
        all_skills_routed,
        "every skill in .agents/skills must be documented in governance/skill-routing.md",
        failures,
        passed,
    )

    p08_live = compile_target(ROOT, "P08")
    p08_knows = p08_live["capsule"].get("KNOWS", "")
    expect(
        "compiler_keeps_k_prefix_and_p08",
        "K011｜" in p08_knows and "K013｜" in p08_knows,
        f"compile_target(P08) must retain K-prefixed ids and include K011/K013 (Ch6/P08): got {p08_knows[:120]!r}",
        failures,
        passed,
    )
    expect(
        "compiler_includes_active_contracts_in_boundaries",
        "[CC-001]" in p08_live["capsule"].get("HARD BOUNDARIES", "") and "[CC-025]" in p08_live["capsule"].get("HARD BOUNDARIES", ""),
        f"compile_target(P08) must surface active canon contracts in HARD BOUNDARIES",
        failures,
        passed,
    )

    stale_gov = (
        "# 第八章｜x\n"
        "CUT-OFF：現行正文第八章結束。\n"
        "CURRENT TEXT：截至第七章尚未登場。\n"
        "CH01｜\nCH02｜\nCH03｜\nCH04｜\nCH05｜\nCH06｜\nCH07｜\nCH08｜\n"
    )
    eight_ch_draft = "\n".join(f"# 第{c}章｜t\n內容。\n" for c in ("一", "二", "三", "四", "五", "六", "七", "八"))
    stale_errs = drift_check(eight_ch_draft, stale_gov, "09-P08", "莉諾兒")
    expect(
        "drift_catches_stale_chapter_cutoff_phrase",
        any("截至第七章" in e for e in stale_errs),
        f"drift_check must flag stale '截至第七章' when draft has Ch8: {stale_errs}",
        failures,
        passed,
    )

    if DRAFT.is_file():
        synced_chs = parse_chapters(DRAFT.read_text(encoding="utf-8"))
        expect(
            "sync_google_doc_parses_live_draft",
            len(synced_chs) == 7 and synced_chs[0].heading.startswith("第一章｜") and all(c.paragraphs for c in synced_chs),
            f"expected 7 non-empty parsed chapters, got {[(c.number, c.heading) for c in synced_chs]}",
            failures,
            passed,
        )
    dup_error = False
    try:
        parse_chapters("# 第一章｜甲\n\n內容一。\n\n# 第一章｜乙\n\n內容二。\n")
    except ValueError:
        dup_error = True
    expect(
        "sync_google_doc_rejects_duplicate_chapter",
        dup_error,
        "parse_chapters must reject duplicate chapter numbers",
        failures,
        passed,
    )

    # The old receiver returned ok=true even after failed tab renames.
    # A webhook now needs a readback-verified chapter count, doc ID and SHA.
    synced = [ChapterPayload(number=1, heading="第一章｜測試", paragraphs=["測試正文。"])]
    good_ack = {
        "ok": True, "verified": True, "verifiedChapters": 1,
        "verifiedTabs": 1, "docId": "doc-test", "sourceSha": "sha-test",
        "updated": ["第一章｜測試"], "warnings": [],
    }
    for name, delta, should_pass in (
        ("verified", {}, True),
        ("legacy_ok_only", {"verified": None}, False),
        ("missing_chapter", {"verifiedChapters": 0}, False),
        ("missing_tab_verification", {"verifiedTabs": 0}, False),
        ("invalid_tab_count", {"verifiedTabs": "1"}, False),
        ("wrong_updated_chapter", {"updated": ["第二章｜別的"]}, False),
        ("wrong_doc", {"docId": "other"}, False),
        ("wrong_sha", {"sourceSha": "stale"}, False),
        ("rename_warning", {"warnings": ["old tab title"]}, False),
        ("receiver_error", {"ok": False}, False),
    ):
        ack = {**good_ack, **delta}
        with patch("sync_google_doc.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = (
                json.dumps(ack).encode("utf-8")
            )
            raised = False
            try:
                push_webhook(
                    synced, "doc-test", "https://example.invalid/sync",
                    "test-secret", "sha-test",
                )
            except RuntimeError:
                raised = True
        expect(
            f"sync_webhook_ack_{name}",
            raised != should_pass,
            f"ack should {'pass' if should_pass else 'fail'}: {ack}",
            failures,
            passed,
        )

    # A local gdocs CLI rename error must not disappear behind a green result.
    def fake_gdocs_command(args: list[str]) -> str:
        if args[:2] == ["readonly", "list-tabs"]:
            return json.dumps([{"tabId": "t.0", "title": "舊標題", "index": 0}])
        if args[:2] == ["mutate", "rename-tab"]:
            raise RuntimeError("rename failed")
        raise AssertionError(f"unexpected command: {args}")

    rename_failed = False
    with patch("sync_google_doc._run_gdocs", side_effect=fake_gdocs_command):
        try:
            push_gdocs_cli(synced, "doc-test", allow_destructive_replace=True)
        except RuntimeError:
            rename_failed = True
    expect(
        "sync_gdocs_cli_rename_failure_is_fatal",
        rename_failed,
        "CLI must fail when rename-tab fails",
        failures,
        passed,
    )

    expect(
        "compiler_includes_style_anchor",
        "ANCHOR-" in p08_live["capsule"].get("STYLE ANCHOR", "")
        and any(s["id"] == "STYLE-ANCHOR" for s in p08_live["sources"]),
        f"compile_target(P08) must inject STYLE ANCHOR from governance/style-anchors.md",
        failures,
        passed,
    )
    expect(
        "compiler_includes_voice_words",
        "VOICE-WORDS：" in p08_live["capsule"].get("VOICE", ""),
        f"VOICE fingerprint slice must retain VOICE-WORDS examples: {p08_live['capsule'].get('VOICE', '')!r}",
        failures,
        passed,
    )
    # Selection must react to actual scene and POV rather than always slicing
    # the first two examples. These tests probe all three distinct anchors.
    for kind, scene, expected in (
        ("dialogue", {"POV": "林恩", "場景類型": "同學互虧對話"}, "ANCHOR-DIALOGUE"),
        ("healing", {"POV": "亞德里安", "定位": "牧師施法治療"}, "ANCHOR-ACTION"),
        ("ensemble", {"POV": "莉諾兒", "主要場景": "廚房裡的日常群像"}, "ANCHOR-ENSEMBLE"),
        ("pov_only", {"POV": "莉諾兒"}, "ANCHOR-ENSEMBLE"),
    ):
        picked = extract_style_anchors(ROOT, fields=scene)
        expect(
            f"style_anchor_select_{kind}",
            picked.startswith(f"[{expected}｜") and picked.count("[ANCHOR-") == 1,
            f"wrong scene-specific anchor: {picked[:90]!r}",
            failures,
            passed,
        )
    expect(
        "style_anchor_no_missing_source",
        extract_style_anchors(SANDBOX, fields={"場景類型": "對話"}) == "",
        "missing style-anchors.md must be optional in minimal compiler sandboxes",
        failures,
        passed,
    )
    dir_fields = scene_fields(
        "SCENE STRUCTURE：Sequel\nTRIGGER：信箋被攤開\nSUBTEXT：怕再次被趕出去\nFORBIDDEN REACTIONS：禁止落淚\n"
    )
    expect(
        "compiler_parses_optional_director_fields",
        dir_fields.get("SCENE STRUCTURE") == "Sequel"
        and dir_fields.get("SUBTEXT") == "怕再次被趕出去"
        and dir_fields.get("FORBIDDEN REACTIONS") == "禁止落淚",
        f"director fields parsed incorrectly: {dir_fields}",
        failures,
        passed,
    )
    slop_hits = scan_lexicon(FIXTURES / "pass_clean.md", text="她嘴角勾起一絲笑意，不由得眼眶微紅。\n")
    slop_groups = {h.group for h in slop_hits}
    literal_hits = scan_lexicon(FIXTURES / "pass_clean.md", text="這幾年以前，便已經一絲一線往王都接過去了。\n")
    expect(
        "lexicon_detects_webnovel_slop_and_spares_literal",
        "STYLE-01 空泛評價形容" in slop_groups and "AI-01 固定微表情" in slop_groups and literal_hits == [],
        f"slop_groups={slop_groups} literal_hits={literal_hits}",
        failures,
        passed,
    )

    # Audit regressions: assert both legitimate and rejected paths.
    test_draft = "# 第一章｜起點\n\n正文。\n"
    test_gov = "CUT-OFF：現行正文第一章結束。\nCH01｜第一章\n"
    expect("audit_planned_range_not_fact", drift_check(test_draft, test_gov + "[PLANNED] Ch8–9\n", "", "莉諾兒") == [], "planned range must not become TEXT-FACT", failures, passed)
    expect("audit_multiple_fact_chapters", any("8" in e for e in drift_check(test_draft, test_gov + "[TEXT-FACT Ch1 / Ch8]\n", "", "莉諾兒")), "all fact chapter references must be checked", failures, passed)
    expect("audit_empty_state_diff_rejected", any("State Diff" in e for e in drift_check(test_draft, "CUT-OFF：現行正文第一章結束。", "", "莉諾兒")), "empty State Diff must not pass", failures, passed)
    expect("audit_future_state_diff_rejected", any("多出" in e for e in drift_check(test_draft, test_gov + "CH08｜未寫\n", "", "莉諾兒")), "future State Diff must not pass", failures, passed)
    expect("audit_invalid_contract_base_rejected", bool(check_immutability("invalid-ref-for-regression-test")), "unreadable base must fail closed", failures, passed)
    bad_chain = {"contracts": [{"id": "X", "status": "superseded", "superseded_by": "X", "scope": {"all": True}, "require": ["x"]}]}
    expect("audit_contract_cycle_rejected", any(h.kind == "schema" for h in validate_schema(bad_chain)), "cyclic supersession must fail", failures, passed)
    missing_reason = {"revision_level": "R2", "target": "chapter-01", "state_change": "none", "backup_ref": "99_備份/x.md"}
    expect("audit_state_change_reason_required", bool(check_revision(missing_reason, [PROSE], ["99_備份/x.md"])), "state bypass needs a reason", failures, passed)
    expect("audit_backup_must_be_new", bool(check_revision({**missing_reason, "state_change_reason": "wording only"}, [PROSE], [])), "previous backup cannot be reused", failures, passed)
    expect("audit_r0_outline_rejected", bool(check_revision({"revision_level": "R0", "target": "ops-runtime", "governance_sync": True, "state_change": "none"}, ["10_現行創作資料/09_序章～第一篇章節大綱｜第二版.md"], [])), "R0 must not edit narrative outline", failures, passed)
    vg = "# 03｜Voice Fingerprints\n亞德里安・梵恩\n甲聲線\n莉諾兒\n乙聲線\n# 04｜"
    expect("audit_pov_not_plot_character", extract_voice_for(vg, "莉諾兒", "亞德里安經過")[1] == ["莉諾兒"], "plot mention cannot inject another POV", failures, passed)
    with patch("sync_google_doc._run_gdocs") as mocked_cli:
        blocked = False
        try:
            push_gdocs_cli([ChapterPayload(1, "第一章｜測試", ["內文。"])], "doc-test")
        except RuntimeError:
            blocked = True
        expect("audit_cli_requires_destructive_opt_in", blocked and not mocked_cli.called, "no CLI access without explicit consent", failures, passed)
    gap_rejected = False
    try:
        parse_chapters("# 第一章｜甲\n內容。\n# 第三章｜乙\n內容。\n")
    except ValueError:
        gap_rejected = True
    expect("audit_sync_chapter_gap_rejected", gap_rejected, "chapter numbers must be consecutive", failures, passed)

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
