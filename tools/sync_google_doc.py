#!/usr/bin/env python3
"""One-way publisher: split live Markdown draft by chapter and sync to Google Doc Tabs.

Canonical draft (`10_現行創作資料/小說正文第三版.md`) stays the single source of truth;
Google Doc is strictly a published output (AGENTS.md §2).

Modes:
    webhook  POST chapters JSON to Google Apps Script Web App (`GDOC_WEBHOOK_URL` /
             `GDOC_WEBHOOK_SECRET`), suitable for GitHub Actions CI.
    gdocs    Push chapters locally via authenticated `gdocs` CLI (`--tab` + `rename-tab`).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prose_checks import CHAPTER_HEAD, DRAFT, chapter_number  # noqa: E402

DEFAULT_DOC_ID = "1Qg63ffCy3DlLNpmr1mBz-_yjHDgRBY-QbFxRNI5jOt4"
CHINESE_NUMS = (
    "",
    "一",
    "二",
    "三",
    "四",
    "五",
    "六",
    "七",
    "八",
    "九",
    "十",
    "十一",
    "十二",
    "十三",
    "十四",
    "十五",
    "十六",
    "十七",
    "十八",
    "十九",
    "二十",
)


@dataclass
class ChapterPayload:
    number: int
    heading: str
    paragraphs: list[str]


def cn_chapter_label(n: int) -> str:
    if 1 <= n < len(CHINESE_NUMS):
        return f"第{CHINESE_NUMS[n]}章"
    return f"第{n}章"


def parse_chapters(text: str) -> list[ChapterPayload]:
    """Split Markdown novel draft by `# 第N章｜章名` into structured chapter payloads."""
    matches = list(CHAPTER_HEAD.finditer(text))
    if not matches:
        raise ValueError("找不到任何 `# 第N章｜章名` 章節標題")

    chapters: list[ChapterPayload] = []
    seen_numbers: set[int] = set()
    for idx, m in enumerate(matches):
        raw_num = m.group(1)
        ch_num = chapter_number(raw_num)
        if ch_num is None:
            raise ValueError(f"無法解析章號：{raw_num!r}")
        if ch_num in seen_numbers:
            raise ValueError(f"重複章號：{ch_num}")
        if ch_num != idx + 1:
            raise ValueError(f"章號不連續：預期 {idx + 1}，實際 {ch_num}")
        seen_numbers.add(ch_num)

        heading = f"第{raw_num}章｜{m.group(2).strip()}"
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        paragraphs = [
            re.sub(r"\n+", "\n", block.strip())
            for block in re.split(r"\n\s*\n+", body)
            if block.strip()
        ]
        if not paragraphs:
            raise ValueError(f"章節沒有內文段落：{heading}")
        chapters.append(ChapterPayload(number=ch_num, heading=heading, paragraphs=paragraphs))

    return chapters


def push_webhook(
    chapters: list[ChapterPayload],
    doc_id: str,
    webhook_url: str,
    webhook_secret: str,
    source_sha: str,
    reserve_excess_tabs: bool = True,
) -> dict:
    payload = {
        "secret": webhook_secret,
        "docId": doc_id,
        "sourceSha": source_sha,
        "reserveExcessTabs": reserve_excess_tabs,
        "chapters": [asdict(ch) for ch in chapters],
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Webhook HTTP {exc.code}: {detail[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Webhook request failed: {exc.reason}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Webhook returned non-JSON response: {raw[:300]!r}") from exc
    if not isinstance(parsed, dict) or parsed.get("ok") is not True:
        raise RuntimeError(f"Webhook returned error: {parsed}")
    if (parsed.get("verified") is not True
            or type(parsed.get("verifiedChapters")) is not int
            or parsed.get("verifiedChapters") != len(chapters)
            or type(parsed.get("verifiedTabs")) is not int
            or parsed["verifiedTabs"] < len(chapters)
            or parsed.get("updated") != [ch.heading for ch in chapters]
            or parsed.get("docId") != doc_id
            or parsed.get("sourceSha") != source_sha
            or parsed.get("warnings")):
        raise RuntimeError(
            "Webhook response is not verified: tab titles and full chapter text "
            "must be read back successfully (redeploy the current Apps Script receiver)"
        )
    return parsed


def _run_gdocs(args: list[str]) -> str:
    exe = shutil.which("gdocs") or "gdocs"
    proc = subprocess.run(
        [exe, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"gdocs {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.stdout


def push_gdocs_cli(
    chapters: list[ChapterPayload],
    doc_id: str,
    reserve_excess_tabs: bool = True,
) -> dict:
    raw_tabs = _run_gdocs(["readonly", "list-tabs", doc_id, "--json"])
    tabs = json.loads(raw_tabs)
    if not isinstance(tabs, list):
        raise RuntimeError(f"Unexpected list-tabs JSON: {raw_tabs[:200]}")

    root_tabs = [t for t in tabs if t.get("nestingLevel", t.get("nesting", 0)) == 0]
    root_tabs.sort(key=lambda t: t.get("index", 0))

    updated: list[str] = []
    created: list[str] = []
    reserved: list[str] = []
    def rename_tab(tab_id: str, new_title: str) -> None:
        # A failed rename is a sync failure; do not call the result successful.
        _run_gdocs(["mutate", "rename-tab", doc_id, tab_id, new_title])

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for idx, ch in enumerate(chapters):
            if idx < len(root_tabs):
                tab_id = root_tabs[idx]["tabId"]
                cur_title = root_tabs[idx].get("title", "")
                if cur_title != ch.heading:
                    rename_tab(tab_id, ch.heading)
            else:
                out = _run_gdocs(
                    ["mutate", "create-tab", doc_id, "--title", ch.heading, "--index", str(idx), "--json"]
                )
                tab_info = json.loads(out)
                tab_id = tab_info["tabId"]
                created.append(ch.heading)

            ops = [{"op": "heading", "text": ch.heading, "level": "2"}]
            for para in ch.paragraphs:
                ops.append({"op": "append", "text": para})

            ops_file = tmp / f"ch_{ch.number}.json"
            ops_file.write_text(json.dumps(ops, ensure_ascii=False), encoding="utf-8")
            _run_gdocs(
                ["mutate", "batch", doc_id, "-f", str(ops_file), "--tab", tab_id, "--replace-all"]
            )
            updated.append(f"{ch.heading} ({tab_id})")

        if reserve_excess_tabs and len(root_tabs) > len(chapters):
            for idx in range(len(chapters), len(root_tabs)):
                tab_id = root_tabs[idx]["tabId"]
                reserve_title = f"[預留] {cn_chapter_label(idx + 1)}（PLANNED）"
                if root_tabs[idx].get("title", "") != reserve_title:
                    rename_tab(tab_id, reserve_title)
                ops = [
                    {"op": "heading", "text": reserve_title, "level": "2"},
                    {
                        "op": "append",
                        "text": f"本分頁保留給後續 [PLANNED] 章節；現行正文已同步至{cn_chapter_label(len(chapters))}。",
                    },
                ]
                ops_file = tmp / f"reserve_{idx + 1}.json"
                ops_file.write_text(json.dumps(ops, ensure_ascii=False), encoding="utf-8")
                _run_gdocs(
                    ["mutate", "batch", doc_id, "-f", str(ops_file), "--tab", tab_id, "--replace-all"]
                )
                reserved.append(f"{reserve_title} ({tab_id})")

    # The CLI's batch exit status alone does not prove tab renaming worked.
    after = json.loads(_run_gdocs(["readonly", "list-tabs", doc_id, "--json"]))
    if not isinstance(after, list):
        raise RuntimeError("gdocs list-tabs readback is not a list")
    root_after = sorted(
        [t for t in after if t.get("nestingLevel", t.get("nesting", 0)) == 0],
        key=lambda t: t.get("index", 0),
    )
    expected_titles = [ch.heading for ch in chapters]
    if reserve_excess_tabs:
        expected_titles.extend(
            f"[預留] {cn_chapter_label(i + 1)}（PLANNED）"
            for i in range(len(chapters), len(root_tabs))
        )
    if [t.get("title") for t in root_after[:len(expected_titles)]] != expected_titles:
        raise RuntimeError("gdocs tab title readback mismatch")
    return {"ok": True, "updated": updated, "created": created, "reserved": reserved, "verifiedTitles": True, "verifiedContent": False, "warnings": []}


def main() -> int:
    parser = argparse.ArgumentParser(description="One-way sync Markdown draft to Google Doc Tabs")
    parser.add_argument("--draft", default=str(DRAFT), help="Path to canonical draft Markdown")
    parser.add_argument("--doc-id", default=os.environ.get("GDOC_ID", DEFAULT_DOC_ID))
    parser.add_argument("--mode", choices=["webhook", "gdocs"], default="webhook")
    parser.add_argument("--dry-run", action="store_true", help="Parse and print plan without syncing")
    parser.add_argument("--strict", action="store_true", help="Fail if webhook credentials are unset")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-reserve-excess", action="store_true")
    args = parser.parse_args()

    draft_path = Path(args.draft)
    text = draft_path.read_text(encoding="utf-8")
    chapters = parse_chapters(text)

    if args.dry_run:
        summary = {
            "ok": True,
            "mode": "dry-run",
            "docId": args.doc_id,
            "chapters": [{"number": c.number, "heading": c.heading, "paragraphs": len(c.paragraphs)} for c in chapters],
        }
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            for c in chapters:
                print(f"DRY-RUN\tCh{c.number}\t{c.heading}\tparagraphs={len(c.paragraphs)}")
        return 0

    if args.mode == "gdocs":
        res = push_gdocs_cli(chapters, args.doc_id, reserve_excess_tabs=not args.no_reserve_excess)
        print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else f"OK\tgdocs-sync-title-only\tupdated={len(res['updated'])}\tcreated={len(res['created'])}\treserved={len(res['reserved'])}")
        return 0

    webhook_url = os.environ.get("GDOC_WEBHOOK_URL", "").strip()
    webhook_secret = os.environ.get("GDOC_WEBHOOK_SECRET", "").strip()
    if not webhook_url or not webhook_secret:
        msg = "SKIP\t未設定 GDOC_WEBHOOK_URL 或 GDOC_WEBHOOK_SECRET（詳見 governance/google-doc-sync.md）"
        print(msg, file=sys.stderr if args.strict else sys.stdout)
        return 1 if args.strict else 0

    source_sha = os.environ.get("SOURCE_SHA") or os.environ.get("GITHUB_SHA", "local")
    res = push_webhook(
        chapters,
        doc_id=args.doc_id,
        webhook_url=webhook_url,
        webhook_secret=webhook_secret,
        source_sha=source_sha,
        reserve_excess_tabs=not args.no_reserve_excess,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else f"OK\twebhook-sync-verified\tchapters={res['verifiedChapters']}\tdoc={args.doc_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
