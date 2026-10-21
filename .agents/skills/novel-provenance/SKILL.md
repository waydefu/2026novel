---
name: novel-provenance
description: Write a committed, auditable record for a chapter revision, covering the three-piece evidence chain (pre-AI draft, conversation log, first machine output). Use after a prose change is accepted, when handing off a chapter, or when the user asks 溯源／證據／記錄改稿. The record documents what was changed, what was deliberately kept, and what was not verified.
license: MIT
compatibility: 需要 Python 3.12+ 執行 tools/write_provenance.py
metadata:
  version: "1.0.0"
  when_to_use: "溯源, 證據, 改稿紀錄, handoff, 三件套"
  argument_hint: "[chapter] [level]"
  policy: "governance/evidence-policy.md"
allowed-tools: Read Grep Glob Edit Write Bash
---

# novel-provenance

把「這一章怎麼改的」寫成可稽核的紀錄，落在 `governance/provenance/`（Markdown，進 git）。

## 為什麼

若未來要投稿，部分平台要求保留三件套：跑 AI 前的原稿、與 AI 的對話過程、對話後的首版輸出。缺任何一件，申辯空間就少。

| 件 | 本專案的位置 |
|---|---|
| 跑 AI 前原稿 | `99_備份/01_正文備份/` 里程碑快照（`novel-backup`） |
| 對話過程 | 分支與 PR 紀錄、agent session log |
| AI 首版輸出 | 本 skill 產生的 `governance/provenance/*.md` |

## 步驟

1. 確認本次的備份路徑（R2 以上必備）與分支／commit。
2. 跑：

```text
py -3 tools/write_provenance.py --chapter "第五章｜不能把她留在這裡" --level R2 --scope "第 6–8 段" --backup "99_備份/01_正文備份/…" --base <修改前 commit> --first-output <首版正文路徑> --agent-log <對話紀錄路徑> --notes "…" --kept "…" --unverified "…"
```

3. 產出的檔名帶 **run id**（時間戳＋雜湊），同一天對同一章重跑不會覆寫舊紀錄；重複寫同一路徑會直接報錯。
4. 手動補三段（工具不會代填）：
   - **改稿意圖**：為什麼改、依據是什麼。
   - **保留理由**：工具命中但語意成立的地方（逐條列；沒有則寫「無」）。
   - **未驗證項目**：沒有驗證的事要明講，不能假裝通過。
5. 三件套（跑 AI 前原稿／AI 首版輸出／對話過程）缺任何一件時，該列會標 `UNVERIFIED`；不得事後補填成已完成。

## 紀律

- 紀錄不刪除；它是歷史證據，不是現行 Canon。
- 不在紀錄裡寫規則表、勾選框或字數表以外的工程噪音；重點是「改了什麼、沒改什麼、沒驗證什麼」。
- CI 綠燈不構成「作品是人寫的」的證明；這份紀錄才是。
