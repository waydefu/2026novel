---
name: novel-draft-mode
description: Write or revise live novel prose in DRAFT MODE using a small Capsule, current draft, and character voice. Use when drafting, rewriting, or editing chapters in 小說正文第三版, P01–P08 scenes, or when the user asks to 起稿／重寫／修正文.
when-to-use: 寫章, 改正文, 重寫場景, DRAFT MODE, 小說正文第三版
argument-hint: "[chapter] [revision-level]"
paths:
  - "10_現行創作資料/小說正文第三版.md"
---

# novel-draft-mode

主筆模式。先讓場景成立，再修句子。不要把治理表寫進正文。

## 進場

1. 若還沒有本場 Capsule，先跑 `novel-canon-pack`。
2. 施工稿只有 `10_現行創作資料/小說正文第三版.md`。
3. 主筆只讀：Capsule、必要 Voice、最近必要正文、作者本輪指示。
4. 規則細節以 `AGENTS.md` 為準，不要把 §13 全文載入主筆上下文。
5. R2 以上或整章重寫前，先跑 `novel-backup`，並把路徑寫進 `governance/change-manifest.yaml` 的 `backup_ref`。
6. 施工前確認 manifest：`revision_level`、`target`、`canon_change`、`governance_sync`。R1 禁止改 01–06。

## 寫的時候

- 一場一種人稱、一名焦點角色。
- 只寫焦點角色能感知、記得、推測或取得的資訊。
- 繁體中文白話。能講清楚就不要寫深。
- 異世界一般診療者用「牧師」；「神官」只給高階聖職。現代段可用醫生／醫院。
- 人名用「亞德里安・梵恩」（全形中點）。
- 讀者可見章名：`第N章｜章名`。P01／P02 只留給大綱與施工索引。
- 不要在正文放 TBD、規則說明、勾選、字數表或工作筆記。

## 停手

遇到這些立刻停，問作者，不要猜：

- 需要新動機、家族、制度、法律身分、宗教位階、魔法規則
- 必須先解 TBD 才能繼續
- 高權威互斥
- 本輪授權的 Revision Level 不夠

## 出場

寫完不要宣稱完成。切到 `novel-qa-mode`。若章級狀態有變，再跑 `novel-state-sync`。
