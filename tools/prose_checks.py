"""Shared paths and mechanical checks. Hits are candidates unless marked hard-fail."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "10_現行創作資料" / "小說正文第三版.md"
SETTINGS = ROOT / "10_現行創作資料" / "01-08_小說設定總表｜角色・關係・劇情資料.md"
OUTLINE = ROOT / "10_現行創作資料" / "09_序章～第一篇章節大綱｜第二版.md"
GOVERNANCE_11 = ROOT / "10_現行創作資料" / "11_小說工程治理總表｜Knowledge・State・QA・TBD.md"
AGENTS = ROOT / "AGENTS.md"
CHANGELOG = ROOT / "00A_設定歷史修改紀錄｜Changelog.md"
LURE_TOKEN = "LURE_TOKEN_SHADOW_PRINCESS_NOT_CANON"

TBD_IN_PROSE = re.compile(r"\[TBD\]|\bTBD-\d+|\bTBD\b")
DISPLAY_P_CODE = re.compile(
    r"^#{1,3}\s*(?:第[一二三四五六七八九十百千0-9]+章.*)?P-?0*\d+",
    re.MULTILINE,
)
WRONG_NAME_DOT = re.compile(r"亞德里安[·.]梵恩")
ASCII_NAME = re.compile(r"\bAdrian\b", re.IGNORECASE)
ANTECEDENT = re.compile(r"再次|依舊|果然|和平常一樣|照例|又一次")
PATTERN_TEMPLATES = [
    (r"不是.{1,20}而是", "STYLE-04 概念摘要候選"),
    (r"意識到|不得不承認|無法否認", "STYLE 銜接套式候選"),
    (r"瞳孔一縮|指尖微蜷|喉結滾動|唇角勾起", "AI-01 固定微表情候選"),
    (r"胸口像被|空氣像凝|時間像停|情緒像潮", "AI-03 模糊感官比喻候選"),
]
CLERIC_MISUSE = re.compile(r"醫師")
HIGH_CLERIC = re.compile(r"神官")
PASTOR = re.compile(r"牧師")
MODERN_OK = re.compile(r"醫生|醫院|診所|急診")


@dataclass
class Hit:
    path: Path
    line: int
    kind: str
    severity: str  # hard | candidate
    text: str

    def format(self) -> str:
        snippet = self.text.strip().replace("\n", " ")
        if len(snippet) > 80:
            snippet = snippet[:77] + "..."
        return f"{self.severity.upper()}\t{self.kind}\t{self.path}:{self.line}\t{snippet}"


def posix_rel(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def classify_rel(rel: str) -> str:
    """prose = enforce hard gates; governance/exempt = do not."""
    rel = rel.replace("\\", "/")
    if rel.startswith("evals/fixtures/fail_"):
        return "prose"
    if rel.startswith("evals/fixtures/pass_"):
        return "prose"
    if rel.startswith("evals/fixtures/pattern_"):
        return "pattern"
    if rel.startswith("evals/fixtures/exempt_"):
        return "exempt"
    if rel.startswith("evals/recovery/"):
        return "prose"
    if rel.startswith("99_備份/") or "/99_備份/" in rel:
        return "exempt"
    if rel.startswith("00A") or "Changelog" in rel:
        return "exempt"
    if "小說正文第三版" in rel and "備份" not in rel and "99_" not in rel:
        return "prose"
    return "governance"


def classify_path(path: Path, root: Path = ROOT) -> str:
    return classify_rel(posix_rel(path, root))


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def scan_hard_gate(
    path: Path,
    text: str | None = None,
    *,
    root: Path = ROOT,
    force_scope: str | None = None,
) -> list[Hit]:
    scope = force_scope or classify_path(path, root)
    if scope in {"exempt", "governance", "pattern"}:
        return []
    text = read_text(path) if text is None else text
    hits: list[Hit] = []
    for i, line in enumerate(text.splitlines(), 1):
        if TBD_IN_PROSE.search(line):
            hits.append(Hit(path, i, "INFO/FORMAT TBD 標籤不得進正文", "hard", line))
        if DISPLAY_P_CODE.search(line):
            hits.append(Hit(path, i, "FORMAT-01 讀者可見章名不得用 P-0N", "hard", line))
        if WRONG_NAME_DOT.search(line) or ASCII_NAME.search(line):
            hits.append(Hit(path, i, "TERM-01 姓名拼寫偏離「亞德里安・梵恩」", "hard", line))
    return hits


def _is_parallel_you(line: str) -> bool:
    return bool(re.search(r"又.{1,8}又", line))


def scan_pattern_risk(path: Path, text: str | None = None) -> list[Hit]:
    text = read_text(path) if text is None else text
    hits: list[Hit] = []
    for i, line in enumerate(text.splitlines(), 1):
        if ANTECEDENT.search(line) and not _is_parallel_you(line):
            hits.append(Hit(path, i, "INFO-01 前情詞候選", "candidate", line))
        for pat, kind in PATTERN_TEMPLATES:
            if re.search(pat, line):
                hits.append(Hit(path, i, kind, "candidate", line))
        if CLERIC_MISUSE.search(line):
            hits.append(Hit(path, i, "TERM-01 醫師用語候選（異世界一般診療者應為牧師）", "candidate", line))
        if HIGH_CLERIC.search(line):
            hits.append(Hit(path, i, "TERM-01 神官用語候選（僅高階聖職；不自動 Fail）", "candidate", line))
        if MODERN_OK.search(line):
            hits.append(Hit(path, i, "ERA 現代醫療詞（現代段允許）", "candidate", line))
        if PASTOR.search(line):
            continue
    return hits


CHAPTER_HEAD = re.compile(r"^# 第([一二三四五六七八九十百千0-9]+)章｜(.+)$", re.MULTILINE)
CN_NUM = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def chapter_number(token: str) -> int | None:
    if token.isdigit():
        return int(token)
    if token in CN_NUM:
        return CN_NUM[token]
    if token.startswith("十") and len(token) == 2:
        return 10 + CN_NUM.get(token[1], 0)
    return None


def split_chapters(text: str) -> dict[int, str]:
    matches = list(CHAPTER_HEAD.finditer(text))
    chapters: dict[int, str] = {}
    for idx, m in enumerate(matches):
        n = chapter_number(m.group(1))
        if n is None:
            continue
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        chapters[n] = text[start:end]
    return chapters


def count_zh_chars(text: str) -> int:
    body = re.sub(r"^#.*$", "", text, flags=re.MULTILINE)
    return len(re.findall(r"[\u4e00-\u9fff]", body))
