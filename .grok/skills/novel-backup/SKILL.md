---
name: novel-backup
description: Create milestone backups under 99_備份 before major prose or governance edits. Use before R2+ scene edits, chapter rewrites, governance refactor, or when the user asks to 備份／快照.
when-to-use: 備份, 快照, 重大修改前, R2, R3, R4
argument-hint: "[draft|rules|governance] [reason]"
---

# novel-backup

里程碑備份。備份沒有 Canon 權威。

## 放哪

規則見 `AGENTS.md` 16.8–16.9：

- 正文 → `99_備份/01_正文備份/`
- 設定／規則（00、01–08、09 等）→ `99_備份/02_設定與規則備份/`
- 治理入口、11、00A、結構整理 → `99_備份/03_治理紀錄備份/`

## 步驟

1. 依 Revision Level 判斷要不要備。R0 通常不必。R1 大範圍整章才備一份。R2 以上或治理重構必備。
2. 複製現行檔，檔名含原因與日期，例如 `小說正文第三版｜第六章重修前備份｜2026-09-01.md`。
3. 不要從備份施工。備份只供回退、比較、作者要求的復原。
4. 復原＝把里程碑檔複製回現行路徑，再跑 `py -3 tools/scan_hard_gate.py` 與 `py -3 evals/run_evals.py`。評測裡的 recovery drill（`evals/recovery/drill.py`）必須保持綠燈；不要在現行 Canon 上練習破壞。
5. 刪舊備份前必須留下至少一個可回退節點，並在 00A 記錄刪除項與保留項。

## 禁止

- 把備份當最新施工稿
- 為每句微調建快照
- 用備份內容回灌已作廢的舊劇情
