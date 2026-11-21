# 治理狀態快照

Snapshot：2026-11-22｜基準：`origin/main` @ `773c4e1`（PR #42 合併後）

本頁是**快照**，只記錄現在的進度、作者授權與未決缺口，供交接用。施工細節以 `10_現行創作資料/11_小說工程治理總表｜Knowledge・State・QA・TBD.md` 的 CURRENT HANDOFF 與 Knowledge／State 為準；規則以 `AGENTS.md` 為準。快照過時時，以 git 歷史與 11 為準，不以本頁為準。

## 1. 進度

| 項目 | 狀態 | 依據 |
| --- | --- | --- |
| 正文第一至八章 | 已在 main（本輪完成 Ch2–Ch8 跨章接縫、資訊前提與碎句節奏精修，`short_para` 80.8% → 63.7%、`longest_run` 9 → 6、西幻段詞庫 0 命中） | `10_現行創作資料/小說正文第三版.md`；11 CURRENT HANDOFF；`00A`（`CHG-2026-11-22-005`） |
| 第八章（09-P08 弧第一場） | 已寫 | 11 CURRENT HANDOFF |
| 09-P08 第二場起 | PLANNED，事件未鎖定，需作者決策或單場試寫確認 | 11 NEXT；09 §7 |
| 原第九章 | 已撤回（作者 2026-10-27 指示），不具正文事實權威，不得搬回 | 00A；11 CURRENT HANDOFF |
| 前八章文學驗收（PR #36、#37 ＋ 本輪精修） | 已合併；`11` 的 `CURRENT WORKING DRAFT` 已更新至 `2026-11-22` | `00A`（`CHG-2026-11-03-001`、`CHG-2026-11-22-005`）；`governance/quality/2026-11-03_前八章編輯驗收與寫作依據.md` |
| 治理層 | Governance 2.0 已落地（2026-09-01）；已完成兩輪品質導向工具與治理重構＋`prose_rhythm.py` 右引號切句修正 | `governance/trust-and-authorization.md`；`00A`（`CHG-2026-11-22-001`～`005`） |

## 2. 作者授權紀錄

授權只適用於列出的那一輪，不延伸到下一輪（見 `governance/trust-and-authorization.md` §2）。

| 日期 | 作者原話（節錄） | 授權範圍 | 不包含 |
| --- | --- | --- | --- |
| 2026-11-22 | 「照 world-unbound 的治理幫我更新 2026novel 的設定」 | 治理與操作層（`governance/`、`AGENTS.md` 一行指標、PR 範本、生成檔、00A 一筆、備份快照） | 正文、Canon、TBD 答案、第九章 |
| 2026-11-22 | 「直接幫你把基準 SHA 一併對齊現在全修」 | 修正 G2 描述、補記 00A 2026-11-03 條目（G3）、對齊 `status.md` 基準 SHA（G4）、說明 11 日期同步限制（G5）、修補 `tools/sync_skills.py` 並部署本地 skill 鏡像 | 正文、Canon、TBD 答案、第九章 |
| 2026-11-22 | 「ci、技能、md、治理還有哪些問題一起看」「先研究，要對小說品質有實質提昇的，幫我全部整理並部份重構『依照你的判斷』」 | 第一輪重構 `tools/`（Context Compiler 注入真實 POV Voice 與支援第一篇 `A1`、詞庫補齊翻譯腔與隱形字元、`chapter_number` 百位數支援、`continuity_probe` 與 `CC-011` 納入 Ch8、`check_revision_gate` 允許 R0 同步 11 標頭）、瘦身 `AGENTS.md` 並加上 `[AUTHORIZATION-SCOPE]`、修復 `09-P08` 標題格式、更新 `11` 與 `tools/README.md`／`governance/README.md`／Skills／evals | 正文內容、角色 Canon、TBD 答案、新第九章 |
| 2026-11-22 | 「合，然後第二輪」 | 第二輪深層重構：修復 `compile_context.py` 的 `K016` 索引切片 bug 與自動注入 active Canon 契約至 `HARD BOUNDARIES`、清除 `11` 與 `09` 內部 9 處殘留之 Ch7 過時描述（含 K001「手機掉到床邊」與補齊 `RK013`）、升級 `check_derived_drift.py` 攔截過時「截至第N章」、升級 `prose_rhythm.py` 顯示最長短句串原文預覽、升級 `count_chapter.py` 支援全書統計、新增 3 項 evals（共 95 項） | 正文內容、角色 Canon、TBD 答案、新第九章 |
| 2026-11-22 | 「可以，然後依你看正文須重構與補強的地方全改」 | R2 正文跨章接縫、資訊前提與碎句節奏精修（Ch2–Ch8）、同步 `11` 標頭日期與 `00A`、建立里程碑備份與溯源紀錄、修正 `tools/prose_rhythm.py` 右引號切句 bug | 角色／世界新 Canon、TBD 答案、新第九章 |

## 3. 未決缺口

| # | 缺口 | 誰可以解決 |
| --- | --- | --- |
| G1 | 單人維護，沒有獨立第二審查者 | 作者 |
| G2 | main 已有啟用中的分支規則 `main-governance-ci`（ruleset id 22027890），要求 `gate-proven` 通過；但 `required_approving_review_count` 為 0，`require_code_owner_review` 為 false，repo 也沒有 CODEOWNERS，受保護檔案的修改不需要任何人批准 | 作者（GitHub 設定） |
| G3 | （已解決）00A 已補記 `CHG-2026-11-03-001` 前八章文學驗收條目 | 已於 `CHG-2026-11-22-002` 補記 |
| G4 | 09-P08 第二場起的事件未鎖定 | 作者 |
| G5 | 第一篇主線入口（TBD-008）未決 | 作者 |
| G6 | 制度與身分類 TBD（TBD-006 莉諾兒正式身分與契約、TBD-007 學院身分、TBD-013 瑟拉菲娜學院身分） | 作者 |

完整 TBD 清單見 11 §08。

## 4. 變更規則

- 每次更新本頁時同步改掉「快照日期」與「基準 SHA」，不得只改其中一半。
- 本頁不取代 00A。重大 Canon、治理或版本結構變更仍寫進 00A。
