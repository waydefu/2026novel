# tools

機械掃描與操作工具層。不創造 Canon，不覆寫 `AGENTS.md`。

本機 Windows 用 `py -3`；CI 用 `python`。

| 指令 | 作用 | CI 性質 |
| --- | --- | --- |
| `scan_hard_gate.py` | 只對現行正文：TBD、P-0N 章名、姓名拼寫、簡體字（FONT-01）、零寬隱形字元（FORMAT-01） | 阻擋式；備份／00A／11 豁免 |
| `canon_contract.py` | 驗證 `governance/canon-contracts.json`（append-only）既存事實契約 | 阻擋式 |
| `continuity_probe.py` | 跨章接縫與線頭斷言（T01–T18） | 阻擋式 |
| `check_derived_drift.py` | 11 與正文／09／設定總表的一致性與 CUT-OFF 檢查 | 阻擋式 |
| `check_revision_gate.py` | R0–R4 manifest vs 實際變更檔、備份保護 | 阻擋式 |
| `check_rule_budget.py` | `AGENTS.md` 行數／指令上限與下沉規則登記表檢查 | 阻擋式 |
| `check_core_invariants.py` | 核心不變條件標記在 `AGENTS.md` 與各工具規則檔的一致性 | 阻擋式 |
| `sync_agent_rules.py` | 由 `governance/agent-rules-source.md` 單一來源生成 Cursor／Copilot／CLAUDE 規則檔 | `--check` 阻擋式 |
| `validate_skills.py` | 驗證 `.agents/skills/*/SKILL.md` 符合 Agent Skills 規格 | 阻擋式 |
| `sync_skills.py` | 為單一工具部署／檢查／清理 skill 鏡像（`.claude/skills` 等） | `--check` 阻擋式 |
| `compile_context.py` | Context Compiler＋provenance（支援 `P01`～`P08`、`A1-01`～`A1-08`），載入當前 POV Voice 並拒絕 `99_備份` | 阻擋式 |
| `prose_lexicon.py` | 中文去 AI 味詞庫候選掃描与 `governance/lexicon.lock` 鎖檔檢查 | `--check-lock` 阻擋；掃描只報告 |
| `prose_rhythm.py` | 句長、短句率、連續短句串、短段占比與對話比量測 | 只報告（供冷讀定位） |
| `style_profile.py` | 以專案自有正負樣本校準的文風基準量測（標註非判據項） | 只報告 |
| `scan_pattern_risk.py` | 前情詞、套式、診療用語候選 | 只報告 |
| `timeline_probe.py` | 跨章季節、月份與年齡標記盤點 | 只報告 |
| `count_chapter.py --chapter N` | 章內漢字字數統計 | 工具查詢，不設硬門檻 |
| `write_provenance.py` | 產出逐章修稿溯源紀錄（三件套雜湊與備份比對）至 `governance/provenance/` | 修稿交付工具 |
| `write_evidence.py` | 產出 SHA-bound CI evidence JSON 至 `governance/evidence/` | CI artifact |

PATTERN RISK 與詞庫／節奏的命中必須人工依 `AGENTS.md` 判定。不要把本目錄的正則當成自動死刑表。
