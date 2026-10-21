# Definition of Done｜各修稿層級的完成定義

借用 Agile 的 DoD 概念：DoD 是**跨工作項目的共同完成定義**，不是「我做完了」。同一個 R level 的所有 PR 都用同一份完成條件；DoD 會隨專案演進，但每次修改都要留下紀錄（ADR 或 00A）。

原則：DoD 只回答「什麼算完成」，不回答「這段寫得好不好」。文學品質由 11 §02 的 Acceptance Tests 與冷讀負責。

## R0｜OPS（工具、規則、治理文件）

- [ ] `governance/change-manifest.yaml` 的 `revision_level: R0`、`target: ops-runtime`。
- [ ] 只改動 ops 範圍（`.agents/`、`.claude/`、`.opencode/`、`.grok/`、`tools/`、`evals/`、`.github/`、`.cursor/`、`governance/`、根 `README.md`／`.gitignore`／`AGENTS.md`／`00A`）或新增備份快照。
- [ ] `py -3 evals/ci_suite.py` 全綠。
- [ ] 新增的閘門有對應的 eval 案例（正樣本必須綠、負樣本必須紅），且 fixture 不進正文範圍。
- [ ] 若改動了量表或詞庫：`governance/lexicon.lock` 與 `governance/rhythm-thresholds.json` 已同步更新，且更新理由寫進本次紀錄。
- [ ] 若改動了 AGENTS.md：通過 `tools/check_rule_budget.py`；被移出的規則已在 `governance/rule-budget.json` 登記。
- [ ] 若改動了多工具規則檔：通過 `tools/sync_agent_rules.py --check`。

## R1｜PROSE EDIT（行文層）

- [ ] 授權範圍內的段落完成修改；事件、Knowledge、資訊揭露時點、關係狀態、Canon 未變。
- [ ] `tools/scan_hard_gate.py` 0 hits；`tools/canon_contract.py` 0 violations。
- [ ] `tools/prose_lexicon.py` 與 `tools/prose_rhythm.py` 的候選已逐條人工判讀；命中但保留者已寫下保留理由。
- [ ] 完成一次自由冷讀（不看規則表，只問哪裡怪、假、卡、像模板）。
- [ ] 已留下溯源紀錄（`tools/write_provenance.py`），含未驗證項目。
- [ ] 不改正文時，不同步 11。

## R2｜SCENE EDIT（場景層）

- [ ] 章級目的、鎖定事件、Knowledge 邊界、章末 State、HARD dependency 皆保留。
- [ ] `governance/change-manifest.yaml` 的 `revision_level: R2`、`target: chapter-NN`、`canon_change: false`、`governance_sync: true`、並填 `backup_ref`。
- [ ] 備份快照已存在於 `99_備份/01_正文備份/`（新增，不修改既有快照）。
- [ ] 11 的 04／05／06／07 同步更新；`tools/check_derived_drift.py` 綠。
- [ ] 新章或大改後，完成 11 §02 A–E 的 Hard Gate 全項逐條判讀。

## R3｜CHAPTER REWRITE（整章）

- [ ] R2 的全部項目成立。
- [ ] 重做整章 Acceptance Tests（A–M 逐項），並完成冷讀。
- [ ] 章長符合作者最新章別目標，且不是靠灌水或硬砍。
- [ ] 章綱對應段落只標 [PLANNED]，未提前標成已發生。

## R4｜STRUCTURAL／CANON REVISION（結構與 Canon）

- [ ] **作者已明確決定答案**（不只是指出問題）。
- [ ] 先改最高權威來源（01–08 或世界設定），再同步 09／11／正文。
- [ ] 附 ADR 條目（`governance/adr/`），Status 與索引已更新。
- [ ] 重大變更寫入 `00A_設定歷史修改紀錄｜Changelog.md`。
- [ ] 舊 Canon 條目以 `superseded` 標記並指向新條目，不直接改寫（見 ADR-0001）。
- [ ] `governance/canon-contracts.json` 相應契約新增或標記 `superseded`。

## 通用

- 任何一層都必須寫清楚：**哪些沒驗證**。未驗證不得假裝通過。
- 證據（`governance/evidence/*.json`）由 CI 產生，綠燈只證明「被檢查的那些事成立」，不證明文學品質。
