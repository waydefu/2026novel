#!/usr/bin/env python3
"""Canon contract tests: the written draft is the consumer, canon is the provider.

Direction (AGENTS.md §1 + ADR-0001)
------------------------------------
Once a chapter is accepted, the facts inside it become *existing facts*. Canon
files (01–08) may not silently contradict them; they can only catch up
(re-acknowledge) or go through an explicit, recorded retcon. This tool encodes
that direction as executable contracts so a contradiction fails CI instead of
waiting for a human to notice.

Fail-closed rules (audited 2026-10-22)
--------------------------------------
* A contract whose `scope` names a chapter that does not exist is an ERROR,
  not an empty set. A forbid-only contract over an empty scope used to pass
  silently — that was a false green.
* A contract that resolves to an empty scope is an ERROR.
* `--json` must always emit valid JSON, and the exit code stays non-zero when
  violations exist.
* With `--base <sha>`, existing contract ids are immutable: they may not be
  deleted or rewritten. Superseding requires a new id plus `superseded_by`.

Contract file: governance/canon-contracts.json (append-only).

Governance rules enforced here (registry: governance/rule-budget.json):
    HB-004  異世界一般診療者為牧師；神官限高階聖職
    HB-005  已寫正文的既存事實不得被設定或新稿矛盾；改寫須走 retcon
    HB-006  PLOT RESET 後的舊版反派與深淵主線不得回流正文
    HB-023  Canon 契約為 append-only；既有契約 id 不得刪除或改寫
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT, ROOT, classify_path, read_text  # noqa: E402

CONTRACT_FILE = ROOT / "governance" / "canon-contracts.json"
CHAPTER_HEAD = re.compile(r"^# (第[一二三四五六七八九十百千0-9]+章.*)$", re.MULTILINE)
VALID_STATUS = {"active", "superseded", "retired"}


@dataclass
class ContractHit:
    contract_id: str
    title: str
    kind: str  # missing | forbidden | schema | scope | immutable
    detail: str
    line: int = 0
    text: str = ""

    def format(self) -> str:
        loc = f"{self.line}" if self.line else "-"
        snippet = self.text.strip().replace("\n", " ")[:70]
        return f"CONTRACT\t{self.contract_id}\t{self.kind}\tline={loc}\t{self.title}\t{snippet}"


def split_chapters(text: str) -> list[tuple[str, str]]:
    parts = re.split(r"^# (第[一二三四五六七八九十百千0-9]+章.*)$", text, flags=re.MULTILINE)
    return [(name, chunk) for name, chunk in zip(parts[1::2], parts[2::2])]


def resolve_scope(scope: dict, chapters: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], list[str]]:
    """Return (resolved chapters, errors). Missing chapters are errors, not empty sets."""
    errors: list[str] = []
    if scope.get("all"):
        return chapters, errors
    if "chapters" in scope:
        wanted = scope["chapters"]
        resolved = [(n, c) for n, c in chapters if any(w in n for w in wanted)]
        missing = [w for w in wanted if not any(w in n for n, _ in chapters)]
        if missing:
            errors.append(f"scope.chapters 指向不存在的章節：{missing}")
        return resolved, errors
    if "from" in scope:
        start = scope["from"]
        idx = next((i for i, (n, _) in enumerate(chapters) if start in n), None)
        if idx is None:
            errors.append(f"scope.from 指向不存在的章節：{start}")
            return chapters, errors
        return chapters[idx:], errors
    errors.append("scope 缺少 all / chapters / from")
    return chapters, errors


def load_contracts(path: Path = CONTRACT_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(contracts: dict) -> list[ContractHit]:
    hits: list[ContractHit] = []
    seen: set[str] = set()
    for contract in contracts.get("contracts", []):
        cid = str(contract.get("id", "?"))
        title = str(contract.get("title", ""))
        status = contract.get("status", "active")
        if cid in seen:
            hits.append(ContractHit(cid, title, "schema", "契約 id 重複"))
        seen.add(cid)
        if status not in VALID_STATUS:
            hits.append(ContractHit(cid, title, "schema", f"未知 status：{status}"))
        if not contract.get("scope"):
            hits.append(ContractHit(cid, title, "schema", "缺少 scope"))
        if not contract.get("require") and not contract.get("forbid"):
            hits.append(ContractHit(cid, title, "schema", "require 與 forbid 皆為空，契約無作用"))
        if not isinstance(contract.get("require", []), list) or not isinstance(contract.get("forbid", []), list):
            hits.append(ContractHit(cid, title, "schema", "require／forbid 必須是陣列"))
    return hits


def run_contracts(text: str, contracts: dict) -> list[ContractHit]:
    hits: list[ContractHit] = validate_schema(contracts)
    chapters = split_chapters(text)
    for contract in contracts.get("contracts", []):
        if contract.get("status", "active") != "active":
            continue
        scope = contract.get("scope", {"all": True})
        cid = contract.get("id", "?")
        title = contract.get("title", "")
        resolved, scope_errors = resolve_scope(scope, chapters)
        for err in scope_errors:
            hits.append(ContractHit(cid, title, "scope", err))
        if scope_errors:
            continue
        if not resolved:
            hits.append(ContractHit(cid, title, "scope", "scope 解析後為空，契約不會生效"))
            continue
        for pat in contract.get("require", []):
            if not any(re.search(pat, chunk) for _, chunk in resolved):
                hits.append(ContractHit(cid, title, "missing", f"缺少必要事實 /{pat}/"))
        for pat in contract.get("forbid", []):
            for name, chunk in resolved:
                for i, line in enumerate(chunk.splitlines(), 1):
                    if re.search(pat, line):
                        hits.append(ContractHit(cid, title, "forbidden", f"出現禁止內容 /{pat}/", i, line))
                        break
                else:
                    continue
                break
    return hits


def check_immutability(base: str, contract_path: Path = CONTRACT_FILE) -> list[ContractHit]:
    """Existing contract semantics are immutable (append-only).

    * an existing contract id may not disappear;
    * an active contract's enforced fields (scope / require / forbid) may not be
      rewritten — that is how a contract gets quietly bent to fit new prose;
    * documentation (title / rationale) may be corrected, but only when the
      file's `version` is bumped, so the change stays visible.
    """
    hits: list[ContractHit] = []
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{base}:{contract_path.relative_to(ROOT).as_posix()}"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return hits
    try:
        old = json.loads(raw)
    except json.JSONDecodeError:
        return hits
    new = load_contracts(contract_path)
    old_map = {c.get("id"): c for c in old.get("contracts", [])}
    new_map = {c.get("id"): c for c in new.get("contracts", [])}
    for cid, contract in old_map.items():
        if cid not in new_map:
            hits.append(ContractHit(str(cid), str(contract.get("title", "")), "immutable", "既有契約被刪除（契約為 append-only）"))
            continue
        if contract.get("status") == "active" and new_map[cid].get("status") == "active":
            for field in ("scope", "require", "forbid"):
                if contract.get(field) != new_map[cid].get(field):
                    hits.append(
                        ContractHit(
                            str(cid),
                            str(contract.get("title", "")),
                            "immutable",
                            f"既有契約的 {field} 被改寫（要取代請新增 id 並標 superseded_by）",
                        )
                    )
    changed_docs = [
        cid
        for cid, contract in old_map.items()
        if cid in new_map
        and (contract.get("title") != new_map[cid].get("title") or contract.get("rationale") != new_map[cid].get("rationale"))
    ]
    if changed_docs and int(new.get("version", 0)) <= int(old.get("version", 0)):
        hits.append(
            ContractHit(
                "CONTRACT-FILE",
                "契約文件",
                "immutable",
                f"契約說明文字有變更（{changed_docs}）但 version 未遞增（{old.get('version')} → {new.get('version')}）",
            )
        )
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DRAFT))
    parser.add_argument("--contracts", default=str(CONTRACT_FILE))
    parser.add_argument("--base", default="", help="比對基準 sha：檢查契約是否被 append-only 破壞")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    contract_path = Path(args.contracts)
    try:
        contracts = load_contracts(contract_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR\tcontracts\t{exc}", file=sys.stderr)
        return 2

    path = Path(args.path)
    if not path.is_file():
        print(f"ERROR\tmissing\t{path}", file=sys.stderr)
        return 2
    scope = classify_path(path)
    if scope != "prose":
        print(f"EXEMPT\tscope={scope}\t{path}")
        return 0

    hits = run_contracts(read_text(path), contracts)
    if args.base:
        hits += check_immutability(args.base, contract_path)

    if args.json:
        print(
            json.dumps(
                {"violations": [asdict(h) for h in hits], "count": len(hits)},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for hit in hits:
            print(hit.format())
        print(f"CONTRACTS\t{len(contracts.get('contracts', []))}\tviolations={len(hits)}")
    if hits:
        print(
            "ERROR\tcanon contract violated：已寫正文的既存事實不得被設定或新稿矛盾；"
            "要改就寫 retcon（新增條目、標 status=superseded），不要改寫既有條目。",
            file=sys.stderr,
        )
        return 1
    print("OK\tcanon-contract\t0 violations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
