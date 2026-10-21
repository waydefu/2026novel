# QA 操作清單

本檔是**施工期可操作**的清單。權威驗收表在 `10_現行創作資料/11_小說工程治理總表｜Knowledge・State・QA・TBD.md` §02（Acceptance Tests A–M），本檔不重複抄寫，只給「這一步跑什麼、看到什麼算數、什麼不算數」。

## 1. 起稿前（作者指示 → Capsule）

1. 確認本次是行文修訂（R1）、場景重寫（R2）、整章重寫（R3）還是 Canon 變更（R4）。判斷錯了比做錯更貴。
2. 跑 `py -3 tools/compile_context.py --target P08 --check-only`，保留 provenance。
3. 確認 `governance/change-manifest.yaml` 的 level／target／canon_change／governance_sync。
4. R2 以上：先備份，快照放 `99_備份/01_正文備份/`，路徑填進 `backup_ref`。
5. 確認沒有 open TBD 會擋住本場（TBD-006／007 目前會擋 P08 的契約與學院身分敘述）。

## 2. 寫作中

- 一場一種人稱、一名焦點角色。
- 只寫焦點角色能感知、記得、推測或取得的資訊。
- 異世界一般診療者＝牧師；「神官」只給高階聖職；現代段可用醫院／醫師／急診。
- 人名寫作「亞德里安・梵恩」（全形中點）。
- 讀者可見章名：`第N章｜章名`。
- 正文不寫 TBD、規則說明、審稿標籤、字數表、工作筆記。
- 遇到需要新增動機／家族／制度／法律身分／宗教位階／魔法規則，或必須先解 TBD，或高權威互斥 → **停下問作者**，不要用「合理」補。

## 3. 寫完後（QA MODE）

依序跑：

```text
py -3 tools/scan_hard_gate.py      # 阻擋式：TBD 標籤／P-0N 章名／姓名拼寫
py -3 tools/canon_contract.py      # 阻擋式：已寫正文的既存事實
py -3 tools/scan_pattern_risk.py   # 候選
py -3 tools/prose_lexicon.py       # 候選（含 --not-evidence 清單）
py -3 tools/prose_rhythm.py        # 候選：只作冷讀定位
py -3 tools/style_profile.py       # 量測：非判據項目標記「非判據」
py -3 tools/count_chapter.py --chapter N
py -3 tools/check_derived_drift.py
py -3 evals/run_evals.py
```

## 4. 判讀紀律（三層）

| 層 | 誰能判 | 例子 |
|---|---|---|
| 機器可算 | 工具直接決定 | TBD 標籤、章名格式、姓名拼寫、契約違規 |
| 機器只能算字面形態 | 工具給候選，人判語意 | 「不是 X 而是 Y」、空泛形容、作者解說句 |
| 機器算不出 | 只有人讀 | 這句是否刻意、這段是否讓人想繼續讀、角色是否活著 |

命中處理三選一，**不得靜默略過**：

- 成立 → 改。
- 不成立 → 保留，並寫下保留理由。
- 需要作者決定 → 標 NEEDS AUTHOR，交回作者。

## 5. 冷讀（不看規則表）

1. 哪裡一眼像 AI 在交作業？
2. 哪裡角色像在替作者整理邏輯？
3. 哪裡太乾、太規矩、太平均？
4. 哪裡明明完全合理，卻沒有任何想繼續讀的慾望？
5. 哪個細節、反應或對話只有這個角色會有？

規則全過但整體不好讀，一樣不算完成。

## 6. 已下沉規則速查（規則 → 執行者）

| 規則 | 執行者 |
|---|---|
| 正文無 TBD／P-0N 章名／姓名拼寫 | `tools/scan_hard_gate.py` |
| 已寫正文的既存事實不得被矛盾；PLOT RESET 邊界 | `tools/canon_contract.py` |
| 牧師／神官用語層級 | `tools/canon_contract.py`＋`tools/prose_lexicon.py` |
| 前情詞、概念摘要、固定微表情、模糊比喻、作者解說句、空泛形容 | `tools/prose_lexicon.py` |
| 碎句製造張力 | `tools/prose_rhythm.py` |
| 比喻／設問／排比／被動／句長均勻度**不是**判據 | `tools/style_profile.py` |
| 規則體量上限、被移出規則的登記 | `tools/check_rule_budget.py` |
| 多工具規則檔同步 | `tools/sync_agent_rules.py` |
| R0–R4 與備份要求 | `tools/check_revision_gate.py` |
| 溯源紀錄 | `tools/write_provenance.py` |
| 完成定義 | `governance/definition-of-done.md` |
| 決議紀錄 | `governance/adr/` |
| 去 AI 味證據分級 | `governance/ai-flavor-evidence.md` |
