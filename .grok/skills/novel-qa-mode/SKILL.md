---
name: novel-qa-mode
description: Post-draft QA for live novel chapters. Runs hard-gate tools, human-judges pattern risk, syncs nothing unless asked, and finishes with a cold read. Use after writing, when reviewing a chapter, 驗收, 冷讀, Fail Code, or anti-AI checks.
when-to-use: QA MODE, 驗收, 冷讀, Hard Gate, Pattern Risk, 反 AI
argument-hint: "[chapter]"
paths:
  - "10_現行創作資料/小說正文第三版.md"
---

# novel-qa-mode

寫後驗收。工具找候選；人依 `AGENTS.md` §13–§14 判定。

## 順序

1. 重新讀修後範圍，不要只看 diff。
2. 跑機械掃描（候選，不是自動判決）：

```text
py -3 tools/scan_hard_gate.py
py -3 tools/scan_pattern_risk.py
py -3 tools/count_chapter.py --chapter N
py -3 tools/check_derived_drift.py
py -3 evals/run_evals.py
```

3. HARD GATE：Canon、POV 越界、Knowledge、資訊前提、術語、明確 OOC、格式。成立就改。
4. PATTERN RISK：只有形成模式、角色同質、或真的變難讀才 Fail。不得為了消滅關鍵字把文字洗成動作報告。
5. 需要同步 11 時才跑 `novel-state-sync`。純行文不改 Knowledge／State／Dependency。
6. 自由冷讀：不問有沒有守規則，只問哪裡怪、假、卡、像模板。
7. 規則全過但不好讀＝未完成。

## 機械掃描不能證明的事

- 關鍵字零命中 ≠ 通過人味
- 工具沒抓到 POV 越界 ≠ 沒有越界
- evals 綠燈 ≠ 場景有生命

## 交付摘要

修改範圍、主要修正模式、章長、Canon／TBD 狀態、跑過哪些檢查、哪些未驗證。正文裡不要出現這些標籤。
