#!/usr/bin/env python3
"""Chinese AI-flavor lexicon. Candidates only — never auto-fail prose.

Design notes
------------
* Every group is a *named failure mode*, not a banned word list. Single hits are
  not evidence; only a pattern is. (humanizer-style: named failure + before/after.)
* The lexicon is pinned: `lexicon_hash()` produces a stable digest recorded in
  `governance/lexicon.lock`. CI fails when the digest drifts, so the ruler
  cannot be quietly loosened. (defluff-style pinnable lexicon.)
* Scope: live draft only. Backups / 00A / 11 are exempt, same as hard gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT, ROOT, classify_path, read_text  # noqa: E402

# ---------------------------------------------------------------------------
# Named Chinese AI failure modes.
# Each entry: (pattern, why-it-reads-as-AI)
# ---------------------------------------------------------------------------

GROUPS: dict[str, list[tuple[str, str]]] = {
    "STYLE-01 空泛評價形容": [
        (r"無比|極其|非常之|無可置疑的", "強度形容詞代替具體描述"),
        (r"宏大|磅礴|壯闊|浩瀚", "大而不當的形容，畫面通常撐不起"),
        (r"深邃|深奧|莫測", "抽象名詞化，讀者無法驗證"),
        (r"駭人|驚世|懾人", "情緒宣告取代事件本身"),
        (r"尊貴|高貴|璀璨", "修飾物而無物"),
    ],
    "STYLE-03 作者解說句": [
        (r"沒有(?:任何)?(?:華麗|深刻|複雜|刻意的)[^。]{0,12}(?:堆砌|鋪陳)", "作者跳出來替作品辯護"),
        (r"(?:全|都)是一(?:個|種)", "作者總結句"),
        (r"沒有(?:半點|絲毫)[^。]{0,10}(?:勉強|生澀|多餘)", "作者宣告『自然』"),
        (r"這(?:不是|並非)[^。]{0,20}(?:而是|只是)", "作品層級的自我標註"),
        (r"(?:總之|換句話說|也就是說)[^。]{0,30}", "譯者式轉述"),
    ],
    "STYLE-04 概念摘要": [
        (r"不是[^。]{1,20}而是", "不是X而是Y 模板"),
        (r"不是因為[^。]{1,20}只是", "不是因為X只是Y 模板"),
        (r"這意味著|這意味著|某種程度(?:上)?|本質上|說到底|歸根究柢", "抽象摘要模板"),
        (r"真正的(?:原因|問題|差別|危險)在於", "作者代讀者下結論"),
    ],
    "AI-01 固定微表情": [
        (r"瞳孔(?:猛地)?一縮|指尖微蜷|喉結滾動|唇角(?:微微)?勾起|嘴角勾起", "固定微表情"),
        (r"眼神一凝|眸光一閃|心頭一顫|身形一僵|眉頭一皺", "固定微表情"),
    ],
    "AI-03 模糊感官比喻": [
        (r"胸口(?:像|彷彿|好像)[^。]{0,10}壓", "模糊身體比喻"),
        (r"空氣(?:像|彷彿|好像)[^。]{0,8}(?:凝固|凝滯)", "模糊環境比喻"),
        (r"時間(?:像|彷彿|好像)[^。]{0,8}(?:停住|靜止|凝固)", "模糊時間比喻"),
        (r"情緒(?:像|彷彿|好像)[^。]{0,8}潮", "模糊情緒比喻"),
        (r"腦(?:中|海)像[^。]{0,10}弦", "模糊思緒比喻"),
    ],
    "AI-05 戲劇化模板": [
        (r"覺醒(?:之日|的瞬間)", "中二模板"),
        (r"宿命|註定(?:要|會|的)", "宿命宣告"),
        (r"棋局|棋子|落子", "將人物比擬成棋子的套路"),
        (r"羈絆|救贖|死結|深淵(?:的呼喚)?", "模板化戲劇詞彙"),
        (r"試煉|覺醒|共鳴|迴響(?:在[^。]{0,10})", "模板化戲劇詞彙"),
    ],
    "AI-06 段尾餘韻": [
        (r"沉默(?:落下|在[^。]{0,8}間)|空氣(?:安靜|靜止)(?:下來)?", "通用段尾餘韻"),
        (r"(?:誰都|誰也)沒有(?:再)?說話", "通用段尾餘韻"),
        (r"(?:某種|一切)[^。]{0,6}(?:改變|變得不同)了", "通用段尾餘韻"),
        (r"故事(?:才|剛)(?:真正|才剛)?開始", "通用段尾宣告"),
    ],
    "TRANSL 翻譯腔/歐化": [
        (r"不僅[^。]{1,20}[，,][^。]{1,20}更(?:是|要|能)", "歐化並列"),
        (r"毫無(?:疑問|例外地)[^。]{0,8}地", "翻譯腔副詞"),
        (r"儼然(?:是|一副)", "翻譯腔副詞"),
        (r"不知(?:道|曉)的是", "全知敘述破口"),
    ],
    "STYLE-05 冒號空轉": [
        (r"(?:以下|如下|包括|包含|分成|具體來說|簡單來說)[:：]\s*$", "引出列表卻不帶資訊（實證 R=9.4，最強特徵）"),
        (r"^(?:這一點|值得注意|需要說明)[：:]", "評價引導句不帶內容"),
        (r"^(?:以下|如下)(?:是|有)[^\n。！？]{0,10}[:：]\s*$", "宣告完就沒了"),
    ],
    "STYLE-06 限定詞堆疊": [
        (r"可能(?:會)?(?:在某種程度|一定程度上|潛在地)[^。]{0,12}(?:影響|造成|改變)", "過度限定詞堆疊"),
        (r"(?:某種|一定程度的|潛在的)[^。]{0,6}(?:程度|層次|層面)", "過度限定詞堆疊"),
    ],
    "STYLE-07 罐頭收尾": [
        (r"總的來說|綜上所述|展望未來|讓我們一起|從今以後[^。]{0,12}(?:將|會)", "通用積極結尾"),
        (r"未來[^。]{0,10}(?:可期|值得期待)", "通用積極結尾"),
    ],
    "ERA-02 現代制度/網路詞": [
        (r"\b(?:APP|KPI|OKR|Bug|UI|UX|SOP|PM)\b", "現代制度詞"),
        (r"打卡|網紅|社群|下班|加班|班表|已讀|外送|客服|進度條", "現代制度詞"),
        (r"冷卻(?:時間)?[，。]?$|解鎖|任務|獎勵|技能樹", "遊戲化措辭"),
    ],
    "ERA-01 診療用語": [
        (r"醫師", "異世界一般診療者應為牧師（現代段用『醫生／醫院』，不在此列）"),
        (r"神官", "僅限高階聖職"),
    ],
    "INFO-01 前情詞": [
        (r"再次|又一次|再度", "前情預設詞，需有已建立依據"),
        (r"依舊|照例|和平常一樣|和往常一樣", "前情預設詞，需有已建立依據"),
        (r"果然", "前情預設詞，需有角色預期"),
    ],
}

# Patterns that are legitimately parallel/choice usage rather than antecedents.
PARALLEL_EXEMPT = re.compile(r"又.{1,8}又")

# ---------------------------------------------------------------------------
# Corpus-backed NON-signals. These must never be used as a reason to rewrite.
# Source: lieflat-less-ai-tone RESEARCH.md (2.83M chars / 629 texts).
# R = AI frequency / human frequency; R < 1 means humans use it MORE.
# ---------------------------------------------------------------------------
NOT_EVIDENCE = {
    "metaphor": ("比喻", "R=0.42；人類用比喻是 AI 的 2.4 倍，獨立成段 8 倍。只在喻體理想化時處理。"),
    "rhetorical_question": ("設問句", "R=0.05；人類是 AI 的 17 倍。刪設問會更像 AI。"),
    "in_sentence_parallel": ("句內排比", "R=0.61；人類不比 AI 少。只有句間重複才成立。"),
    "passive": ("被動句", "R=0.70；能表達受事與責任時應保留。"),
    "nominalisation": ("動詞名詞化", "R=0.52；人類更多，術語不要拆。"),
    "colloquial_connective": ("口語連接詞", "R=0.26；AI 反而更少，方向是補不是刪。"),
    "sentence_uniformity": ("句長均勻度", "R=0.87；與 AI 身分無關，不得為了製造節奏而調句長。"),
    "paragraph_uniformity": ("段長均勻度", "R=0.94；與 AI 身分無關。"),
}

COMPILED: dict[str, list[tuple[re.Pattern[str], str]]] = {
    group: [(re.compile(pat), why) for pat, why in items] for group, items in GROUPS.items()
}


@dataclass
class LexHit:
    path: Path
    line: int
    group: str
    why: str
    text: str

    def format(self) -> str:
        snippet = self.text.strip().replace("\n", " ")
        if len(snippet) > 90:
            snippet = snippet[:87] + "..."
        return f"CANDIDATE\t{self.group}\t{self.path.name}:{self.line}\t{snippet}"


def lexicon_hash() -> str:
    """Stable digest of the lexicon. Recorded in governance/lexicon.lock."""
    payload = json.dumps(GROUPS, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def scan_lexicon(path: Path, text: str | None = None) -> list[LexHit]:
    if text is None:
        text = read_text(path)
    hits: list[LexHit] = []
    for i, line in enumerate(text.splitlines(), 1):
        for group, items in COMPILED.items():
            for rx, why in items:
                if not rx.search(line):
                    continue
                if group == "INFO-01 前情詞" and PARALLEL_EXEMPT.search(line):
                    continue
                hits.append(LexHit(path, i, group, why, line))
                break  # one hit per group per line keeps the report readable
    return hits


def group_counts(hits: list[LexHit]) -> dict[str, int]:
    out: dict[str, int] = {}
    for h in hits:
        out[h.group] = out.get(h.group, 0) + 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DRAFT))
    parser.add_argument("--print-hash", action="store_true")
    parser.add_argument("--lock", default=str(ROOT / "governance" / "lexicon.lock"))
    parser.add_argument("--update-lock", action="store_true")
    parser.add_argument("--check-lock", action="store_true", help="fail if the lexicon digest drifted from the lock file")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--not-evidence", action="store_true", help="列出不可作為改寫依據的特徵")
    args = parser.parse_args()

    if args.not_evidence:
        for key, (label, why) in NOT_EVIDENCE.items():
            print(f"NOT-EVIDENCE\t{label}\t{why}")
        print("NOTE\t以上項目不得作為改寫或刪除的理由。")
        return 0

    if args.print_hash:
        print(lexicon_hash())
        return 0

    lock_path = Path(args.lock)
    if args.update_lock:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(lexicon_hash() + "\n", encoding="utf-8")
        print(f"WROTE\t{lock_path}")
        return 0

    if args.check_lock:
        if not lock_path.is_file():
            print(f"ERROR\tmissing lock\t{lock_path}", file=sys.stderr)
            return 1
        expected = lock_path.read_text(encoding="utf-8").strip()
        actual = lexicon_hash()
        if expected != actual:
            print(
                f"ERROR\tlexicon drift：lock={expected} actual={actual}\n"
                "尺子被改動但未更新鎖檔。若這是刻意的，依 governance/definition-of-done.md 同步更新 "
                "governance/lexicon.lock 並在紀錄寫明理由與影響。",
                file=sys.stderr,
            )
            return 1
        print(f"OK\tlexicon-lock\t{actual[:12]}")
        return 0

    path = Path(args.path)
    if not path.is_file():
        print(f"ERROR\tmissing\t{path}", file=sys.stderr)
        return 2
    scope = classify_path(path)
    if scope != "prose":
        print(f"EXEMPT\tscope={scope}\t{path}")
        return 0

    hits = scan_lexicon(path)
    if args.json:
        print(json.dumps({"counts": group_counts(hits), "total": len(hits)}, ensure_ascii=False, indent=2))
    else:
        for hit in hits:
            print(hit.format())
        print(f"CANDIDATES\t{len(hits)}\t{path.name}")
    print("NOTE\t詞庫命中只是候選；依 AGENTS.md 判定是否形成慣性，單次不算錯。")
    print("NOTE\t比喻、設問、排比、被動、句長均勻度不是 AI 判別指標，不得作為改寫理由（--not-evidence）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
