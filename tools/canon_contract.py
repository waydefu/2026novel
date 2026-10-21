#!/usr/bin/env python3
"""Canon contract tests: the written draft is the consumer, canon is the provider.

Direction (AGENTS.md §2 + ADR-0001)
------------------------------------
Once a chapter is accepted, the facts inside it become *existing facts*. Canon
files (01–08) may not silently contradict them; they can only catch up
(re-acknowledge) or go through an explicit, recorded retcon. This tool encodes
that direction as executable contracts so a contradiction fails CI instead of
waiting for a human to notice.

Contract file: governance/canon-contracts.json (append-only; supersede, do not
rewrite history — every change needs a new entry with a new id).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import DRAFT, ROOT, classify_path, read_text  # noqa: E402

CONTRACT_FILE = ROOT / "governance" / "canon-contracts.json"
CHAPTER_HEAD = re.compile(r"^# (第[一二三四五六七八九十百千0-9]+章.*)$", re.MULTILINE)


@dataclass
class ContractHit:
    contract_id: str
    title: str
    kind: str  # missing | forbidden
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


def resolve_scope(scope: dict, chapters: list[tuple[str, str]]) -> list[tuple[str, str]]:
    if scope.get("all"):
        return chapters
    if "chapters" in scope:
        wanted = scope["chapters"]
        return [(n, c) for n, c in chapters if any(w in n for w in wanted)]
    if "from" in scope:
        start = scope["from"]
        idx = next((i for i, (n, _) in enumerate(chapters) if start in n), 0)
        return chapters[idx:]
    return chapters


def load_contracts(path: Path = CONTRACT_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_contracts(text: str, contracts: dict) -> list[ContractHit]:
    chapters = split_chapters(text)
    hits: list[ContractHit] = []
    for contract in contracts.get("contracts", []):
        if contract.get("status", "active") != "active":
            continue
        scope = resolve_scope(contract.get("scope", {"all": True}), chapters)
        cid = contract.get("id", "?")
        title = contract.get("title", "")
        for pat in contract.get("require", []):
            found = False
            for name, chunk in scope:
                if re.search(pat, chunk):
                    found = True
                    break
            if not found:
                hits.append(ContractHit(cid, title, "missing", f"缺少必要事實 /{pat}/"))
        for pat in contract.get("forbid", []):
            for name, chunk in scope:
                for i, line in enumerate(chunk.splitlines(), 1):
                    if re.search(pat, line):
                        hits.append(ContractHit(cid, title, "forbidden", f"出現禁止內容 /{pat}/", i, line))
                        break
                else:
                    continue
                break
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DRAFT))
    parser.add_argument("--contracts", default=str(CONTRACT_FILE))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.is_file():
        print(f"ERROR\tmissing\t{path}", file=sys.stderr)
        return 2
    scope = classify_path(path)
    if scope != "prose":
        print(f"EXEMPT\tscope={scope}\t{path}")
        return 0

    contracts = load_contracts(Path(args.contracts))
    hits = run_contracts(read_text(path), contracts)
    if args.json:
        print(json.dumps({"violations": [asdict(h) if hasattr(h, "__dict__") else h.__dict__ for h in hits]}, ensure_ascii=False, indent=2))
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
