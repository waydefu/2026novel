# governance｜治理層索引

本資料夾是**操作層**：可機檢的規則、可追溯的決議、可稽核的證據。它不創造 Canon，不覆寫 `AGENTS.md`／`01-08`／`09`／`11`。

| 檔案 | 用途 |
|---|---|
| `agent-rules-source.md` | 單一事實來源：產生 `.cursor/rules/`、`.github/copilot-instructions.md`、`CLAUDE.md`（`tools/sync_agent_rules.py`） |
| `core-invariants.json` | 核心不變條件（帶穩定標記），必須同時存在於根規則與各工具規則檔（`tools/check_core_invariants.py`） |
| `adr/` | 方向性決議與 Status 生命週期（proposed／accepted／superseded） |
| `definition-of-done.md` | R0–R4 各自的完成定義 |
| `qa-checklists.md` | 施工期可操作清單（起稿前／寫作中／寫完後／判讀紀律／冷讀） |
| `skill-routing.md` | 九個 skill 的路由、重疊裁決、部署與規格紅線 |
| `quality-evaluation.md` | 作品品質驗證：可機檢／盲讀比較／誠實的誤報率指標 |
| `evidence-policy.md` | 三件套（原稿／對話過程／首版輸出）與可稽核性 |
| `ai-flavor-evidence.md` | 哪些中文特徵真的判別 AI 味、哪些不成立（本專案裁決） |
| `canon-contracts.json` | 可執行的 Canon 契約（已寫正文的既存事實不得被矛盾） |
| `lexicon.lock` | 詞庫雜湊鎖檔：尺子不得私下放寬 |
| `rhythm-thresholds.json` | 節奏量測門檻（只作冷讀定位，不作改寫依據） |
| `style-profile.json` | 以本專案正負樣本校準的風格基準 |
| `rule-budget.json` | 規則體量上限與「被移出規則的登記表」 |
| `research/` | 外部研究摘要與出處（參考，非 Canon） |
| `evidence/` | CI 產生的 SHA 綁定證據（JSON，不進 git） |
| `provenance/` | 逐章修稿溯源紀錄（Markdown，進 git） |
| `capsules/` | Context Compiler 輸出（不提交、不具 Canon 權威） |
| `change-manifest.yaml` | 本次變更的修稿層級與同步狀態（CI 讀） |
| `main-ruleset.json` | `main` 分支門鎖設定檔 |

## 變更規則

- 改本資料夾＝R0 ops 變更，須更新 `change-manifest.yaml`（`revision_level: R0`、`target: ops-runtime`）。
- 涉及方向性決定 → 開 ADR，不直接改既有決議。
- 涉及量表或詞庫 → 同步更新鎖檔與門檻檔，並在本次紀錄寫明理由。
- 任何從 `AGENTS.md` 移出的規則，必須在 `rule-budget.json` 的 `hoisted_rules` 登記去向，否則 `tools/check_rule_budget.py` 判定為遺失。
