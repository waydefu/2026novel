---
name: novel-state-sync
description: Sync operational governance file 11 after a chapter is accepted. Updates Knowledge, Reader Knowledge, State Diff, Dependency, and TBD without creating Canon. Use after QA passes, when handing off a chapter, or when the user asks to 同步 11／更新治理／State Diff.
when-to-use: 同步 11, State Diff, Knowledge Ledger, 章完成, handoff
argument-hint: "[chapter]"
paths:
  - "10_現行創作資料/11_小說工程治理總表｜Knowledge・State・QA・TBD.md"
---

# novel-state-sync

只更新 11 的衍生狀態。11 不創造 Canon，不得覆寫 00／01–06／09。

## 何時同步

- 新章或改寫被 QA 接受之後
- 角色 Knowledge、讀者已知、章末狀態、後章 HARD 前提、OPEN TBD 有實際變化

不同步：純錯字、標點、不改語義的行文。

## 步驟

1. 以通過後的 `10_現行創作資料/小說正文第三版.md` 為事實來源（[TEXT-FACT]）。
2. 對照 `AGENTS.md` 權威順序與 11 的同步協議。
3. 只改真正變動的分頁：04 Knowledge、05 Reader Knowledge、06 State Diff、07 Dependency；有新未定問題才動 08 TBD。
4. 正文已發生的事標 [TEXT-FACT]；章綱已核准未發生的維持 [PLANNED]。
5. 不得把計畫提前標成已發生，不得用「合理」把 TBD 升格。
6. Canon／關係／世界規則若要改，先停手：那是作者改 01–06 或世界設定的事，不是本 skill。
7. 同步後立刻跑 `py -3 tools/check_derived_drift.py`。11 與正文／09 明顯不一致時停止，標 NEEDS_REVIEW，不得把 11 改成「比較好寫」的版本。
8. 只有 Canon、治理或版本結構改變才更新 `00A_設定歷史修改紀錄｜Changelog.md`。

## 衝突

高權威互斥或缺作者決定：標 [TBD]／[CONFLICT]，停止依賴該項的後續施工。
