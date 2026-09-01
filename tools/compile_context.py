#!/usr/bin/env python3
"""Deterministic Context Compiler. Never loads 99_備份 / 00A / 90_參考資料."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import LURE_TOKEN, ROOT  # noqa: E402

FORBIDDEN_PREFIXES = ("99_備份/", "90_參考資料/")
FORBIDDEN_NAMES = ("00A_設定歷史修改紀錄｜Changelog.md",)


def posix_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def assert_allowed(rel: str) -> None:
    rel = rel.replace("\\", "/")
    if rel.startswith(FORBIDDEN_PREFIXES) or rel in FORBIDDEN_NAMES or rel.startswith("00A"):
        raise RuntimeError(f"compiler refused forbidden source: {rel}")


def read_allowed(root: Path, rel: str) -> str:
    assert_allowed(rel)
    path = root / rel
    if not path.is_file():
        raise FileNotFoundError(rel)
    text = path.read_text(encoding="utf-8")
    if LURE_TOKEN in text:
        raise RuntimeError(f"compiler loaded lure token from {rel}")
    return text


def extract_block(text: str, start: str, end_markers: list[str]) -> str:
    idx = text.find(start)
    if idx < 0:
        return ""
    rest = text[idx:]
    cut = len(rest)
    for marker in end_markers:
        j = rest.find(marker, len(start))
        if j != -1:
            cut = min(cut, j)
    return rest[:cut].strip()


def first_lines(text: str, n: int) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines[:n])


def compile_target(root: Path, target: str) -> dict:
    target_norm = target.strip().upper().replace("CHAPTER-", "P").replace("CH", "P")
    if target_norm in {"8", "P8", "P08"}:
        target_norm = "P08"
    elif target_norm in {"7", "P7", "P07"}:
        target_norm = "P07"
    else:
        if re.fullmatch(r"P0?\d+", target_norm):
            target_norm = f"P{int(target_norm[1:]):02d}"
        else:
            raise ValueError(f"unsupported target: {target}")

    settings_rel = "10_現行創作資料/01-08_小說設定總表｜角色・關係・劇情資料.md"
    outline_rel = "10_現行創作資料/09_序章～第一篇章節大綱｜第二版.md"
    gov_rel = "10_現行創作資料/11_小說工程治理總表｜Knowledge・State・QA・TBD.md"
    draft_rel = "10_現行創作資料/小說正文第三版.md"
    agents_rel = "AGENTS.md"

    settings = read_allowed(root, settings_rel)
    outline = read_allowed(root, outline_rel)
    gov = read_allowed(root, gov_rel)
    draft = read_allowed(root, draft_rel)
    agents = read_allowed(root, agents_rel)

    sources = []
    capsule: dict[str, str] = {}

    sources.append({"id": "RULE-00", "cite": "AGENTS.md / Draft Capsule", "path": agents_rel, "anchor": "AGENTS.md"})
    _ = agents  # loaded only to prove allowlist read; not inlined

    linoir = extract_block(settings, "# 04｜莉諾兒", ["# 05｜"])
    adrian = extract_block(settings, "# 01｜亞德里安", ["# 02｜"])
    if adrian:
        sources.append({"id": "CANON-01", "cite": "01–06 / 亞德里安", "path": settings_rel, "anchor": "01｜亞德里安"})
    if linoir:
        sources.append({"id": "CANON-04", "cite": "01–06 / 莉諾兒", "path": settings_rel, "anchor": "04｜莉諾兒"})

    plot = extract_block(outline, f"## 09-{target_norm}", ["## 09-P", "# 3｜", "# 4｜"])
    if not plot:
        plot = extract_block(outline, f"## 09-{target_norm}｜", ["## 09-P", "# 3｜"])
    if plot:
        sources.append({"id": f"PLOT-{target_norm}", "cite": f"09 / {target_norm}", "path": outline_rel, "anchor": f"09-{target_norm}"})

    know_ids = ["K012", "K013", "K014"] if target_norm == "P08" else ["K010", "K011", "K012", "K013"]
    knows = []
    for kid in know_ids:
        nxt = f"K{int(kid[1:]) + 1:03d}"
        block = extract_block(gov, f"{kid}｜", [f"{nxt}｜", "# 05｜"])
        if block:
            knows.append(first_lines(block, 4))
            title = block.splitlines()[0]
            sources.append({"id": f"KNOW-{kid[1:]}", "cite": f"11 / Knowledge / {kid}", "path": gov_rel, "anchor": title[:40]})

    handoff = extract_block(gov, "CURRENT HANDOFF", ["# 01｜"])
    if handoff:
        sources.append({"id": "GOV-HANDOFF", "cite": "11 / CURRENT HANDOFF", "path": gov_rel, "anchor": "CURRENT HANDOFF"})

    hard = []
    for line in (handoff + "\n" + plot).splitlines():
        if "硬前提" in line or "不得" in line or "HARD" in line:
            hard.append(line.strip(" -#"))
    capsule["POV"] = "依 09 目標場；一場一人稱一名焦點。"
    capsule["NOW"] = first_lines(plot, 3) if plot else first_lines(handoff, 3)
    capsule["WANT"] = "只完成作者指定的本場目標；不把 P08 整段弧一次寫完。" if target_norm == "P08" else "完成本場已核准事件，不預支後章。"
    capsule["KNOWS"] = "\n".join(knows[:6])
    capsule["HARD BOUNDARIES"] = "\n".join(hard[:4]) or "未獲授權不得改 Canon；TBD 不得進正文。"
    capsule["VOICE"] = "只載入本場 POV 的注意偏差；不要整份 Voice Fingerprint。"
    capsule["DESTINATION"] = first_lines(extract_block(plot, "EXIT：", ["## 禁止", "# 3｜"]) or "本場結束於場景自然出口，不要求 State Diff 式過關。", 2)
    capsule["FREEDOM"] = "生活細節、誤解、停滯與無大結果的小事可自由處理。"

    _ = draft  # presence-checked; compiler does not dump whole draft into capsule

    loaded = sorted({s["path"] for s in sources})
    for rel in loaded:
        assert_allowed(rel)

    blob = json.dumps({"capsule": capsule, "sources": sources}, ensure_ascii=False)
    if LURE_TOKEN in blob:
        raise RuntimeError("compiler output contains backup lure token")

    return {
        "target": target_norm,
        "loaded_paths": loaded,
        "excluded_roots": ["99_備份/", "90_參考資料/", "00A"],
        "sources": sources,
        "capsule": capsule,
    }


def render_capsule(payload: dict) -> str:
    lines = [f"# Draft Capsule｜{payload['target']}", ""]
    for key in ("POV", "NOW", "WANT", "KNOWS", "HARD BOUNDARIES", "VOICE", "DESTINATION", "FREEDOM"):
        lines.append(f"## {key}")
        lines.append(str(payload["capsule"].get(key, "")).strip() or "（來源不足，保持 TBD 於工作記錄）")
        lines.append("")
    lines.append("## Provenance")
    for src in payload["sources"]:
        lines.append(f"- {src['id']} ← {src['cite']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="P08")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    root = Path(args.root)
    try:
        payload = compile_target(root, args.target)
    except Exception as exc:  # noqa: BLE001 — compiler must fail closed
        print(f"ERROR\tcompiler\t{exc}", file=sys.stderr)
        return 1
    text = render_capsule(payload)
    if args.out_dir:
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{payload['target']}.capsule.md").write_text(text, encoding="utf-8")
        (out / f"{payload['target']}.provenance.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if args.check_only:
        print(f"OK\tcompiler\t{payload['target']}\tsources={len(payload['sources'])}")
        for src in payload["sources"]:
            print(f"{src['id']} ← {src['cite']}")
        return 0
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
