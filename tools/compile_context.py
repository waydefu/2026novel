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


SCENE_FIELDS = (
    "章節目的", "定位", "施工進度", "POV", "時間／地點", "WANT", "OBSTACLE", "KNOWLEDGE",
    "KNOWLEDGE BOUNDARY", "HARD OUTCOME", "RELATIONSHIP BOUNDARY", "CREATIVE FREEDOM", "EXIT",
    "DRAFT WARNING", "禁止寫法", "主要場景", "CHANGE", "RELATIONSHIP", "篇幅感", "序章完成狀態",
    "SCENE STRUCTURE", "TRIGGER", "SUBTEXT", "PROTECTIVE STRATEGY", "FORBIDDEN REACTIONS",
    "場景類型", "STYLE TYPE",
)


def scene_fields(block: str) -> dict[str, str]:
    """Pull named fields out of a 09 scene card.

    Supports both normal outline lines (`欄位：內容` / `- 項目`) and H2-prefixed
    lines (`## 欄位：內容` / `## - 項目`).
    """
    fields: dict[str, str] = {}
    current: str | None = None
    for line in block.splitlines():
        m = re.match(r"^(?:##\s*)?(?:-\s*)?([^：:]{1,28})[：:]\s*(.*)$", line)
        if m:
            raw_key = m.group(1).strip()
            base_key = re.sub(r"（.*）|\(.*\)", "", raw_key).strip()
            if base_key in SCENE_FIELDS:
                current = base_key
                fields.setdefault(current, "")
                if m.group(2).strip():
                    fields[current] += ("\n" if fields[current] else "") + m.group(2).strip()
                continue
        if current and re.match(r"^(?:##\s*)?-\s+", line):
            fields[current] += ("\n" if fields[current] else "") + re.sub(r"^(?:##\s*)?-\s*", "", line).strip()
    return fields


def first_lines(text: str, n: int) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines[:n])


def knowledge_ids_for(gov_text: str, target: str) -> list[str]:
    """Pick the Knowledge Ledger entries that actually talk about the target.

    Entries whose block mentions the target id (e.g. "P08" or corresponding
    "Ch8") win; otherwise the last four entries are used. Hardcoding ids per
    chapter made the compiler silently return an empty KNOWS for any target
    nobody had listed.
    """
    ids = re.findall(r"^(K\d{3})｜", gov_text, flags=re.MULTILINE)
    if not ids:
        return []
    blocks: dict[str, str] = {}
    for kid in ids:
        nxt = f"K{int(kid[1:]) + 1:03d}"
        block = extract_block(gov_text, f"{kid}｜", [f"{nxt}｜", "# 05｜"])
        blocks[kid] = block
    search_tokens = [target] if target else []
    m_p = re.match(r"^P0?(\d+)", target or "")
    if m_p:
        ch_n = int(m_p.group(1))
        search_tokens.extend([f"Ch{ch_n}", f"CH0{ch_n}", f"Ch{ch_n - 1}–{ch_n}", f"Ch{ch_n}–"])
    targeted = [
        kid
        for kid in ids
        if any(tok and tok in blocks.get(kid, "") for tok in search_tokens)
    ]
    if targeted:
        first = ids.index(targeted[0])
        keep = ids[max(0, first - 2) : first] + targeted  # targeted entries plus two entries of context
        seen: set[str] = set()
        uniq = [k for k in keep if not (k in seen or seen.add(k))]
        return uniq[-6:]
    return ids[-4:]


VOICE_SECTIONS = (
    ("亞德里安", "亞德里安・梵恩", ["克蕾西雅\n", "瑟拉菲娜\n", "莉諾兒\n", "艾琳娜\n", "# 04｜"]),
    ("克蕾西雅", "克蕾西雅", ["瑟拉菲娜\n", "莉諾兒\n", "艾琳娜\n", "# 04｜"]),
    ("瑟拉菲娜", "瑟拉菲娜", ["莉諾兒\n", "艾琳娜\n", "# 04｜"]),
    ("莉諾兒", "莉諾兒", ["艾琳娜\n", "# 04｜"]),
    ("艾琳娜", "艾琳娜", ["# 04｜"]),
)


def extract_voice_for(gov_text: str, pov_text: str, plot_text: str) -> tuple[str, list[str]]:
    """Extract only the active POV character's Voice Fingerprint from 11 §03."""
    voice_block = extract_block(gov_text, "# 03｜Voice Fingerprints", ["# 04｜"])
    if not voice_block:
        return "只載入本場 POV 的注意偏差；不要整份 Voice Fingerprint。", []
    matched_names: list[str] = []
    snippets: list[str] = []
    for short_name, header, stop_markers in VOICE_SECTIONS:
        if short_name in pov_text or (not matched_names and short_name in plot_text):
            sec = extract_block(voice_block, header, stop_markers)
            if sec:
                matched_names.append(short_name)
                keep_lines = []
                for ln in sec.splitlines():
                    ln_s = ln.strip()
                    if not ln_s or ln_s.startswith("CURRENT TEXT") or ln_s.startswith("TEXT-FACT"):
                        continue
                    keep_lines.append(ln_s)
                snippets.append("\n".join(keep_lines[:14]))
    if not snippets:
        return "只載入本場 POV 的注意偏差；不要整份 Voice Fingerprint。", []
    return "\n\n".join(snippets), matched_names


# Scores are editorial cues, not canon or automatic prose-quality judgments.
# Explicit scene-type words outweigh POV affinity; one relevant example is enough.
STYLE_ANCHOR_SCENE_CUES = {
    "ANCHOR-DIALOGUE": ("對話", "交談", "閒聊", "互虧", "問答", "談話", "商量", "聊天", "討論"),
    "ANCHOR-ACTION": ("神術", "施法", "魔法", "治療", "受傷", "急救", "危機", "感官", "查探", "頭痛"),
    "ANCHOR-ENSEMBLE": ("群像", "多人", "廚房", "僕從", "侍女", "共餐", "日常", "相處", "家務", "生活"),
}
STYLE_ANCHOR_POV_HINTS = {
    "林恩": "ANCHOR-DIALOGUE",
    "亞德里安": "ANCHOR-ACTION",
    "莉諾兒": "ANCHOR-ENSEMBLE",
}


def extract_style_anchors(
    root: Path,
    anchor_rel: str = "governance/style-anchors.md",
    fields: dict[str, str] | None = None,
    limit: int = 1,
) -> str:
    """Choose a concise positive example by scene cues first, POV second.

    Do not use the full chapter or draft to select an anchor: that can introduce
    another character's future knowledge and a misleading narrative voice.
    Unspecified scenes fall back to the first general-purpose example.
    """
    path = root / anchor_rel
    if not path.is_file() or limit <= 0:
        return ""
    text = read_allowed(root, anchor_rel)
    blocks = re.findall(r"^##\s+(ANCHOR-[^\n]+)\n.*?```text\n(.*?)\n```", text, flags=re.M | re.S)
    info = fields or {}
    scene_text = "\n".join(
        info.get(key, "")[:400]
        for key in ("場景類型", "STYLE TYPE", "定位", "主要場景", "SCENE STRUCTURE", "WANT", "OBSTACLE")
    )
    pov_text = info.get("POV", "")
    ranked = []
    for index, (title, body) in enumerate(blocks):
        anchor_id = title.split("｜", 1)[0].strip()
        score = sum(3 for cue in STYLE_ANCHOR_SCENE_CUES.get(anchor_id, ()) if cue in scene_text)
        score += sum(1 for pov, preferred in STYLE_ANCHOR_POV_HINTS.items() if pov in pov_text and preferred == anchor_id)
        ranked.append((-score, index, title, body))
    ranked.sort()
    return "\n\n".join(
        f"[{title.strip()}]\n{body.strip()}"
        for _, _, title, body in ranked[:limit]
    )


def normalize_target(target: str) -> str:
    t = target.strip().upper()
    if t.startswith("09-"):
        t = t[3:]
    t = t.replace("CHAPTER-", "P").replace("CH", "P")
    if re.fullmatch(r"\d+", t):
        return f"P{int(t):02d}"
    if re.fullmatch(r"P0?\d+[A-Z]?", t):
        m = re.match(r"^P0?(\d+)([A-Z]?)$", t)
        if m:
            return f"P{int(m.group(1)):02d}{m.group(2)}"
    if re.fullmatch(r"A\d+-0?\d+", t):
        m = re.match(r"^A(\d+)-0?(\d+)$", t)
        if m:
            return f"A{int(m.group(1))}-{int(m.group(2)):02d}"
    raise ValueError(f"unsupported target: {target}")


def compile_target(root: Path, target: str) -> dict:
    target_norm = normalize_target(target)

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

    plot_stops = ["## 09-P", "## 09-A", "# 3｜", "# 4｜", "# 5｜", "# 6｜"]
    plot = extract_block(outline, f"## 09-{target_norm}", plot_stops)
    if not plot:
        plot = extract_block(outline, f"## 09-{target_norm}｜", plot_stops)
    if not plot:
        # Fail closed: a capsule without the target's outline is a capsule that
        # looks authoritative but says nothing about the scene being written.
        raise RuntimeError(
            f"compiler: no outline block for target {target_norm} in {outline_rel}; "
            "refusing to emit a capsule without its scene card"
        )
    sources.append({"id": f"PLOT-{target_norm}", "cite": f"09 / {target_norm}", "path": outline_rel, "anchor": f"09-{target_norm}"})

    char_specs = [
        ("CANON-01", "01｜亞德里安", "# 01｜亞德里安", ["# 02｜"], True),
        ("CANON-02", "02｜克蕾西雅", "# 02｜克蕾西雅", ["# 03｜"], "克蕾西雅" in plot),
        ("CANON-03", "03｜瑟拉菲娜", "# 03｜瑟拉菲娜", ["# 04｜"], "瑟拉菲娜" in plot),
        ("CANON-04", "04｜莉諾兒", "# 04｜莉諾兒", ["# 05｜"], True),
        ("CANON-05", "05｜艾琳娜", "# 05｜艾琳娜", ["# 06｜"], "艾琳娜" in plot),
    ]
    for cid, anchor, start_m, end_m, should_load in char_specs:
        if should_load and extract_block(settings, start_m, end_m):
            sources.append({"id": cid, "cite": f"01–06 / {anchor.split('｜')[1]}", "path": settings_rel, "anchor": anchor})

    # Knowledge ids are derived from the target, not hardcoded per chapter.
    know_ids = knowledge_ids_for(gov, target_norm)
    knows = []
    for kid in know_ids:
        nxt = f"K{int(kid[1:]) + 1:03d}"
        block = extract_block(gov, f"{kid}｜", [f"{nxt}｜", "# 05｜"])
        if block:
            knows.append(first_lines(block, 4))
            title = block.splitlines()[0]
            sources.append({"id": f"KNOW-{kid[1:]}", "cite": f"11 / Knowledge / {kid}", "path": gov_rel, "anchor": title[:40]})
    if not knows:
        raise RuntimeError(
            f"compiler: no Knowledge Ledger entries resolved for target {target_norm}; "
            "refusing to emit a capsule with empty KNOWS"
        )

    handoff = extract_block(gov, "CURRENT HANDOFF", ["# 01｜"])
    if handoff:
        sources.append({"id": "GOV-HANDOFF", "cite": "11 / CURRENT HANDOFF", "path": gov_rel, "anchor": "CURRENT HANDOFF"})

    fields = scene_fields(plot)
    hard: list[str] = []
    for source in (fields.get("HARD OUTCOME", ""), handoff):
        for line in source.splitlines():
            stripped = line.strip(" -#")
            if stripped and ("硬前提" in line or "不得" in line or "HARD" in line):
                hard.append(stripped)
    for line in (handoff + "\n" + plot).splitlines():
        if "TBD" in line and ("不得" in line or "BLOCK" in line or "保持 TBD" in line):
            hard.append(line.strip(" -#"))

    capsule["POV"] = fields.get("POV") or "依 09 目標場；一場一人稱一名焦點。"
    capsule["NOW"] = fields.get("時間／地點") or first_lines(plot, 3) or first_lines(handoff, 3)
    capsule["WANT"] = fields.get("WANT") or (
        "只完成作者指定的本場目標；不把 P08 整段弧一次寫完。"
        if target_norm == "P08"
        else "完成本場已核准事件，不預支後章。"
    )
    capsule["KNOWS"] = "\n".join(knows[:6])
    # Also append RELEVANT ACTIVE CONTRACTS from canon-contracts.json so the writer sees hard boundaries directly
    contracts_path = root / "governance" / "canon-contracts.json"
    if contracts_path.is_file():
        try:
            c_data = json.loads(contracts_path.read_text(encoding="utf-8"))
            for c_item in c_data.get("contracts", []):
                if c_item.get("status", "active") != "active":
                    continue
                c_scope = c_item.get("scope", {})
                if c_scope.get("all") or target_norm == "P08":
                    hard.append(f"[{c_item.get('id')}] {c_item.get('title')}")
        except (OSError, json.JSONDecodeError):
            pass

    seen: set[str] = set()
    uniq = [x for x in hard if not (x in seen or seen.add(x))]
    capsule["HARD BOUNDARIES"] = "\n".join(uniq[:16]) or "未獲授權不得改 Canon；TBD 不得進正文。"
    voice_text, voice_names = extract_voice_for(gov, capsule["POV"], plot)
    capsule["VOICE"] = voice_text
    for vname in voice_names:
        sources.append({"id": f"VOICE-{vname}", "cite": f"11 / Voice Fingerprints / {vname}", "path": gov_rel, "anchor": f"03｜Voice Fingerprints / {vname}"})
    capsule["DESTINATION"] = fields.get("EXIT") or "本場結束於場景自然出口，不要求 State Diff 式過關。"
    capsule["FREEDOM"] = fields.get("CREATIVE FREEDOM") or "生活細節、誤解、停滯與無大結果的小事可自由處理。"

    director_keys = ("SCENE STRUCTURE", "TRIGGER", "PROTECTIVE STRATEGY", "SUBTEXT", "FORBIDDEN REACTIONS")
    director_lines = [f"- {k}：{fields[k].strip()}" for k in director_keys if fields.get(k, "").strip()]
    if director_lines:
        capsule["DIRECTOR"] = "\n".join(director_lines)

    anchor_rel = "governance/style-anchors.md"
    anchor_text = extract_style_anchors(root, anchor_rel, fields=fields)
    if anchor_text:
        capsule["STYLE ANCHOR"] = anchor_text
        sources.append(
            {
                "id": "STYLE-ANCHOR",
                "cite": "governance/style-anchors.md (Pass 2 Positive Cadence)",
                "path": anchor_rel,
                "anchor": "STYLE ANCHORS",
            }
        )

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
        "capsule_chars": len(render_capsule_body(capsule)),
    }


def _capsule_keys(capsule: dict) -> tuple[str, ...]:
    base = ("POV", "NOW", "WANT", "KNOWS", "HARD BOUNDARIES", "VOICE", "DESTINATION", "FREEDOM")
    extra = tuple(k for k in ("DIRECTOR", "STYLE ANCHOR") if capsule.get(k))
    return base + extra


def render_capsule_body(capsule: dict) -> str:
    parts = []
    for key in _capsule_keys(capsule):
        parts.append(f"## {key}\n\n{str(capsule.get(key, '')).strip()}")
    return "\n\n".join(parts) + "\n"


def render_capsule(payload: dict) -> str:
    lines = [f"# Draft Capsule｜{payload['target']}", ""]
    capsule = payload["capsule"]
    for key in _capsule_keys(capsule):
        lines.append(f"## {key}")
        lines.append(str(capsule.get(key, "")).strip() or "（來源不足，保持 TBD 於工作記錄）")
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
        print(f"OK\tcompiler\t{payload['target']}\tsources={len(payload['sources'])}\tcapsule_chars={payload['capsule_chars']}")
        for src in payload["sources"]:
            print(f"{src['id']} ← {src['cite']}")
        return 0
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
