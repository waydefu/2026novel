# 治理狀態快照

Snapshot：2026-11-22｜基準：`origin/main` @ `1cfaf7e`（PR #37 合併後）

本頁是**快照**，只記錄現在的進度、作者授權與未決缺口，供交接用。施工細節以 `10_現行創作資料/11_小說工程治理總表｜Knowledge・State・QA・TBD.md` 的 CURRENT HANDOFF 與 Knowledge／State 為準；規則以 `AGENTS.md` 為準。快照過時時，以 git 歷史與 11 為準，不以本頁為準。

## 1. 進度

| 項目 | 狀態 | 依據 |
| --- | --- | --- |
| 正文第一至八章 | 已在 main | `10_現行創作資料/小說正文第三版.md`；11 CURRENT HANDOFF |
| 第八章（09-P08 弧第一場） | 已寫 | 11 CURRENT HANDOFF |
| 09-P08 第二場起 | PLANNED，事件未鎖定，需作者決策或單場試寫確認 | 11 NEXT；09 §7 |
| 原第九章 | 已撤回（作者 2026-10-27 指示），不具正文事實權威，不得搬回 | 00A；11 CURRENT HANDOFF |
| 前八章文學驗收（PR #36、#37） | 已合併 | `governance/quality/2026-11-03_前八章編輯驗收與寫作依據.md`；`change-manifest.yaml` |
| 治理層 | Governance 2.0 已落地（2026-09-01）；本次新增信任、授權與證據規則 | `governance/trust-and-authorization.md` |

## 2. 作者授權紀錄

授權只適用於列出的那一輪，不延伸到下一輪（見 `governance/trust-and-authorization.md` §2）。

| 日期 | 作者原話（節錄） | 授權範圍 | 不包含 |
| --- | --- | --- | --- |
| 2026-11-22 | 「照 world-unbound 的治理幫我更新 2026novel 的設定」 | 治理與操作層（`governance/`、`AGENTS.md` 一行指標、PR 範本、生成檔、00A 一筆、備份快照） | 正文、Canon、TBD 答案、第九章 |

## 3. 未決缺口

| # | 缺口 | 誰可以解決 |
| --- | --- | --- |
| G1 | 單人維護，沒有獨立第二審查者 | 作者 |
| G2 | GitHub 端沒有 CODEOWNERS 或分支保護規則，受保護檔案只靠本 repo 文件與 PR 審查 | 作者（GitHub 設定） |
| G3 | 00A 沒有 2026-11-03 前八章文學驗收的條目；該次紀錄只在 `governance/quality/` 與 change-manifest | 作者決定是否補記 |
| G4 | 09-P08 第二場起的事件未鎖定 | 作者 |
| G5 | 第一篇主線入口（TBD-008）未決 | 作者 |
| G6 | 制度與身分類 TBD（TBD-006 莉諾兒正式身分與契約、TBD-007 學院身分、TBD-013 瑟拉菲娜學院身分） | 作者 |

完整 TBD 清單見 11 §08。

## 4. 變更規則

- 每次更新本頁時同步改掉「快照日期」與「基準 SHA」，不得只改其中一半。
- 本頁不取代 00A。重大 Canon、治理或版本結構變更仍寫進 00A。
