# 治理狀態快照

Snapshot：2026-11-25｜基準：`origin/main` @ `ca13da9`（PR #55 已合併）。快照基準指施工前 main；本輪後續 PR 須另行驗收。

本頁是**快照**，只記錄現在的進度、作者授權與未決缺口，供交接用。施工細節以 `10_現行創作資料/11_小說工程治理總表｜Knowledge・State・QA・TBD.md` 的 CURRENT HANDOFF 與 Knowledge／State 為準；規則以 `AGENTS.md` 為準。快照過時時，以 git 歷史與 11 為準，不以本頁為準。

## 1. 進度

| 項目 | 狀態 | 依據 |
| --- | --- | --- |
| 正文第一至七章（R4 因果重建版） | 已寫定稿（將現代死亡與七歲甦醒拆為 Ch1–Ch2，恢復原稿對話節奏並補齊魔法施放／人名進場／父母去向的場內因果來源，全第三人稱限知） | `10_現行創作資料/小說正文第三版.md`；`09`、`11`、`00A`（`CHG-2026-11-22-008`） |
| 09-P08（入學前多年日常與啟程） | PLANNED，事件骨架已對齊至 09，待作者啟動後續章節 | 11 NEXT；09 §2（09-P08） |
| 群像設定、大綱與衍生治理層（01-08 / 09 / 11） | 已同步 R4 因果重建 7 章版，TBD-004 生效章別對應 Ch5 | `01-08` §十、`09`、`11` |
| 治理契約、探針與評測（v6） | `canon-contracts.json` 升級 v6（`CC-012`～`CC-018` 標 `superseded`，新增 `CC-019`～`CC-026`）；同步 `continuity_probe.py`、`check_derived_drift.py`、`evals/run_evals.py` | `governance/canon-contracts.json` |
| 寫作工程系統 v3.0（三階段工作流＋FACS＋Style Anchor＋Deep POV 手術；PR #48 已合併） | 新增 `style-anchors.md`、`facs-body-lexicon.md`、`scene-beat-director.md`；升級 `compile_context.py`、`prose_lexicon.py`（重算 `lexicon.lock`）、`11`（`VOICE-WORDS`＋同步 Ch7 `CURRENT HANDOFF`）、4 項核心 Skills、`AGENTS.md`／多工具規則檔與 `evals`（117 項，含 Google Docs 發布回應驗收） | `governance/`、`tools/`、`.agents/skills/`、`evals/` |
| Google 文件發布（PR #49 已合併，PR #50 深度修正） | #49 的真實 GitHub Action 仍因接收端回覆未帶 `verified` 而失敗，Ch2／Ch3／Ch7／預留 Ch8 分頁名稱不一致；#50 用 `requiredRevisionId`、未變更正文 no-op、最小差異、最新 main 重抓＋佇列降低覆寫風險；**正式 Web App 尚未驗收** | `governance/google-doc-sync.md`；[Actions #45223235356](https://github.com/waydefu/2026novel/actions/runs/45223235356) |

## 2. 作者授權紀錄

授權只適用於列出的那一輪，不延伸到下一輪（見 `governance/trust-and-authorization.md` §2）。

| 日期 | 作者原話（節錄） | 授權範圍 | 不包含 |
| --- | --- | --- | --- |
| 2026-11-22 | 「照 world-unbound 的治理幫我更新 2026novel 的設定」 | 治理與操作層（`governance/`、`AGENTS.md` 一行指標、PR 範本、生成檔、00A 一筆、備份快照） | 正文、Canon、TBD 答案、第九章 |
| 2026-11-22 | 「直接幫你把基準 SHA 一併對齊現在全修」 | 修正 G2 描述、補記 00A 2026-11-03 條目（G3）、對齊 `status.md` 基準 SHA（G4）、說明 11 日期同步限制（G5）、修補 `tools/sync_skills.py` 並部署本地 skill 鏡像 | 正文、Canon、TBD 答案、第九章 |
| 2026-11-22 | 「ci、技能、md、治理還有哪些問題一起看」「先研究，要對小說品質有實質提昇的，幫我全部整理並部份重構『依照你的判斷』」 | 第一輪重構 `tools/`（Context Compiler 注入真實 POV Voice 與支援第一篇 `A1`、詞庫補齊翻譯腔與隱形字元、`chapter_number` 百位數支援、`continuity_probe` 與 `CC-011` 納入 Ch8、`check_revision_gate` 允許 R0 同步 11 標頭）、瘦身 `AGENTS.md` 並加上 `[AUTHORIZATION-SCOPE]`、修復 `09-P08` 標題格式、更新 `11` 與 `tools/README.md`／`governance/README.md`／Skills／evals | 正文內容、角色 Canon、TBD 答案、新第九章 |
| 2026-11-22 | 「合，然後第二輪」 | 第二輪深層重構：修復 `compile_context.py` 的 `K016` 索引切片 bug 與自動注入 active Canon 契約至 `HARD BOUNDARIES`、清除 `11` 與 `09` 內部 9 處殘留之 Ch7 過時描述（含 K001「手機掉到床邊」與補齊 `RK013`）、升級 `check_derived_drift.py` 攔截過時「截至第N章」、升級 `prose_rhythm.py` 顯示最長短句串原文預覽、升級 `count_chapter.py` 支援全書統計、新增 3 項 evals（共 95 項） | 正文內容、角色 Canon、TBD 答案、新第九章 |
| 2026-11-22 | 「可以，然後依你看正文須重構與補強的地方全改」 | R2 正文跨章接縫、資訊前提與碎句節奏精修（Ch2–Ch8）、同步 `11` 標頭日期與 `00A`、建立里程碑備份與溯源紀錄、修正 `tools/prose_rhythm.py` 右引號切句 bug | 角色／世界新 Canon、TBD 答案、新第九章 |
| 2026-11-22 | 「以上全修」 | R4 全架構重構（ADR-0002）：統一第三人稱限知視角（`AGENTS.md`＋多工具規則同步）、作廢漢字／筷子／鉛筆線等穿幫並改採通用語字母拼讀、補齊梵恩雙親王都／邊境火漆家書與非流寇疑點線、壓縮序章為 Ch1–Ch6＋P07/P08 `[PLANNED]`、升級 `canon-contracts.json` v5 與評測／探針、更新 `01-08`、`09`、`11`、`00A` 與重寫正文 Ch1–Ch6 | 第一篇正文與各家族未決姓氏 |
| 2026-11-22 | 「開始設定GOOGLE文件自動同步」 | 新增 `.github/workflows/sync-google-doc.yml`、`tools/sync_google_doc.py`、`tools/google_apps_script_sync.gs`、`governance/google-doc-sync.md` 與 `evals` 測試，並以本機 `gdocs` CLI 同步 Ch1–Ch6 至 Google 文件（第 7、8 分頁保留為 `[預留]` 不刪除） | 需作者於 Google 文件部署 Apps Script 並填入 GitHub Secrets 後完成 Webhook 遠端觸發 |
| 2026-11-22 | 「主要是形容事實不會用乾巴巴」「前因後果呢？先別改，先看規則」「先寫看看寫完再對一次規則」 | 依因果順序與資訊邊界重建序章 7 章（Ch1 現代死亡與 Ch2 七歲甦醒拆章，補齊聖徽施法與人名／去向在場來源，恢復原稿對話呼吸），同步 `09`、`11`、`canon-contracts.json` v6、探針與評測 | 第一篇正文與各家族未決姓氏 |
| 2026-11-24 | 「可以，權限暫時不用管，記錄即可」 | 修復 PR #45 留下的 Google 文件同步標題／內文驗證缺口，新增錯誤回報與測試、記錄共享權限風險；僅限 ops／同步程式與文件 | 不修改小說正文、Canon、實際 Google Drive 共用權限或 Secrets |
| 2026-11-24 | 「先研究然後全方位審查」「開始優化」 | 針對已合併 PR #49 研究官方文件並強化 Google 同步：並發、最小文字差異、Docs 修訂衝突防護、模擬測試與部署說明 | 不修改小說正文、Canon、正式 Google 文件內容、共同編輯權限或密鑰 |
| 2026-11-23 | 「工程系統全面升級」 | 整合 Scene-Sequel＋高張力七階段導演（選配）、FACS 生理×道具轉譯、Deep POV 一秒濾鏡詞檢測、Pass 1–3 上下文隔離、正向 `STYLE ANCHOR` 與 `VOICE-WORDS` 注入、詞庫擴充並保留本專案中文實證紅線；同步更新 `tools/`、`governance/`、`.agents/skills/`、`.claude/skills/`、`AGENTS.md`、多工具規則檔、`11`（僅 `VOICE-WORDS` 與 `CURRENT HANDOFF` 對齊）與 `evals` | 正文內容、新角色或世界 Canon、TBD 答案 |

## 3. 未決缺口

| # | 缺口 | 誰可以解決 |
| --- | --- | --- |
| G1 | 單人維護，沒有獨立第二審查者 | 作者 |
| G2 | main 已有啟用中的分支規則 `main-governance-ci`（ruleset id 22027890），要求 `gate-proven` 通過；但 `required_approving_review_count` 為 0，`require_code_owner_review` 為 false，repo 也沒有 CODEOWNERS，受保護檔案的修改不需要任何人批准 | 作者（GitHub 設定） |
| G3 | （已解決）00A 已補記 `CHG-2026-11-03-001` 前八章文學驗收條目 | 已於 `CHG-2026-11-22-002` 補記 |
| G4 | 09-P08 第二場起的事件未鎖定 | 作者 |
| G5 | 第一篇主線入口（TBD-008）未決 | 作者 |
| G6 | 制度與身分類 TBD（TBD-006 莉諾兒正式身分與契約、TBD-007 學院身分、TBD-013 瑟拉菲娜學院身分） | 作者 |
| G7 | Google 文件已知分享權限：「知道連結的任何人可編輯」，作者 2026-11-24 決定暫緩權限處理；本 PR 僅改善同步驗證並記錄現況，不更動任何分享設定 | 作者日後另行授權 |
| G8 | 自動同步接收器需將更新後 `google_apps_script_sync.gs` 手動發布為新的 Apps Script Web App 版本，再執行真實端對端驗收；合併 GitHub PR 不會自動更新已部署腳本 | 作者部署與驗證 |

完整 TBD 清單見 11 §08。

## 4. 變更規則

- 每次更新本頁時同步改掉「快照日期」與「基準 SHA」，不得只改其中一半。
- 本頁不取代 00A。重大 Canon、治理或版本結構變更仍寫進 00A。

## PR #51 稽核處置

依作者 2026-11-24「開始優化」，本輪為 R0 工程修補：Docs 同步安全、治理閘門、CI 證據、上下文編譯、Skills 與工具契約。PR50 稽核提出的正文、Canon 與歷史 ADR 變更未在此輪修改；Apps Script 正式部署與實機端對端驗收仍未完成。參考：[PR #51](https://github.com/waydefu/2026novel/pull/51)。

## 2026-11-25 後續稽核施工

PR #51 已合併；主分支 [治理 CI](https://github.com/waydefu/2026novel/actions/runs/45334051422) 通過，但 [正式發布](https://github.com/waydefu/2026novel/actions/runs/45334051442) 仍因 webhook 未驗證回覆失敗。本輪 R2 修補稽核 S4-F02 的四處限知資訊邊界，統一受傷側與 11 的明確正文事實，保留所有事件、既有 Canon、TBD 與發布權限。四個原生分頁舊名、正式部署、剩餘算法與 ADR 問題未在此輪宣稱完成；Ch4 的兩週停練與 09 的數日描述差異留待大綱對齊。

## 2026-11-25 合併與稽核證據

- [#52](https://github.com/waydefu/2026novel/pull/52) 已入 main；[#53](https://github.com/waydefu/2026novel/pull/53) 原合入舊分支，已由 [#54](https://github.com/waydefu/2026novel/pull/54) 完整移植。合併後 [main CI](https://github.com/waydefu/2026novel/actions/runs/45557114114) 通過。新量測樣本未重新校準。
- 正式 Docs 七章逐段文字（去空行／首尾空白）與 #52 後 main 一致；四個原生分頁標題未同步。隔離副本改名呼叫回傳內部錯誤，讀回標題與文字均未改；原因尚未確認，不視為 GAS E2E。見 `google-doc-sync.md`。
- 本輪 R0 補足 Canon 診斷、規則副本及統一測試入口；未改 Canon、章綱、正文、TBD 或分享權限。

## 七章正文／大綱一致性與閱讀修訂

本輪作者「開始」對應七章冷讀與既存事實對齊。R3 是因觸及 09 的技術層級；實際未重寫整章，保留全部事件、角色、章名、揭露順序和 Canon。已修正文的場內邏輯、童年焦點語感與 Ch7 解說；09、11 依原文對齊。01-08 的暫定七歲、第六章通知與第一人稱殘留列 R4 待追認，不修改既存設定。獨立新上下文冷讀及長度目標尚未驗收。
