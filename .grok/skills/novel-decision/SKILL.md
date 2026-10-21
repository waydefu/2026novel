---
name: novel-decision
description: Record a directional decision as an ADR under governance/adr with a status lifecycle, and keep the changelog and rules in sync. Use when a rule, direction, threshold, lexicon, canon boundary or process is being decided rather than merely edited, or when the user asks 決議／ADR／變更紀錄／規則要改. Authors' explicit decisions outrank agent proposals.
license: MIT
compatibility: 需要 Python 3.12+ 執行 tools/check_rule_budget.py 與 tools/sync_agent_rules.py
metadata:
  version: "1.0.0"
  when_to_use: "ADR, 決議, 規則要改, 門檻, 詞庫, changelog, 方向"
  argument_hint: "[decision-title]"
allowed-tools: Read Grep Glob Edit Write Bash
---

# novel-decision

把「方向性決定」寫成 ADR。純行文、錯字、標點、格式修正不進 ADR。

## 什麼需要 ADR

- 改變權威方向（例如 Canon 與正文的先後關係）。
- 改變修稿流程、閘門、層級或完成定義。
- 放寬或收緊量表、詞庫、門檻（尺子變了要留痕）。
- 新增或取代 Canon 邊界。
- 改變工具之間的規則來源關係。

## 步驟

1. 確認這件事是「決定」而不是「修改」。修改不需要 ADR。
2. 若決定會改 `AGENTS.md`：
   - 跑 `py -3 tools/check_rule_budget.py`（行數與指令上限）。
   - 被移出的規則在 `governance/rule-budget.json` 的 `hoisted_rules` 登記去向。
   - 跑 `py -3 tools/sync_agent_rules.py` 重新產生各工具規則檔（單一事實來源）。
3. 新增 `governance/adr/NNNN-標題.md`，用 `governance/adr/README.md` 的模板：Context / Decision / Consequences / Alternatives considered / Verification。
4. Status 用 `proposed` 或 `accepted`；被取代時標 `superseded` 並填 `superseded_by`，不要改寫舊 ADR 的內容。
5. 更新 `governance/adr/README.md` 的索引。
6. 若是量表或詞庫變更：更新 `governance/lexicon.lock`／`governance/rhythm-thresholds.json`／`governance/style-profile.json`，並在本次紀錄寫明理由與影響（哪些門檻變寬、會不會讓舊稿突然紅）。
7. 若是 Canon 或治理層級的變更：另外寫 `00A_設定歷史修改紀錄｜Changelog.md` 一筆。
8. 跑 `py -3 evals/ci_suite.py`。

## 禁止

- 用 ADR 記錄日常行文修改。
- 為了讓 CI 變綠而放寬尺子（尺子變了要寫理由、寫影響）。
- 在 ADR 裡塞入正文內容或大段設定。
