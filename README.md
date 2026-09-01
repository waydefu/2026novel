# 2026 西幻小說專案

本儲存庫用來管理小說正文、設定、章節大綱、創作規則、參考資料與歷史備份。2026-09-01 已由 [Google Drive 專案資料夾](https://drive.google.com/drive/folders/1U_SBT-cHPmT-hfcjHpr6NPMg31HUmaMd) 完整匯入，文件統一轉為 UTF-8 Markdown，方便逐行修改、審閱與建立 Pull Request。

## 目錄

- `AGENTS.md`：所有代理與協作者修改小說前必須遵守的現行創作規則。
- `10_現行創作資料/`：正文、設定總表、章節大綱與工程治理資料。
- `90_參考資料/`：角色或創作參考資料。
- `99_備份/`：依 Google Drive 原結構保留的歷史快照，通常不直接修改。
- `00A_設定歷史修改紀錄｜Changelog.md`：現行設定與規則變更紀錄。

## 修改與 PR

1. 先閱讀根目錄的 `AGENTS.md`。
2. 從 `main` 建立新分支，例如 `rewrite/p05`、`canon/linoir-age`。
3. 只修改本次工作涉及的 Markdown 檔案；若影響 Canon、規則或歷史紀錄，一併同步相關檔案。
4. 提交後推送分支並建立 Pull Request。
5. 依 PR 範本確認敘事、Canon、資訊順序、格式與反 AI 味要求。

現行內容應在 `10_現行創作資料/` 修改；`99_備份/` 用於追溯，不作為日常編輯入口。
