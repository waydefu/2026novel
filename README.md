# 2026 西幻小說專案

本儲存庫用來管理小說正文、設定、章節大綱、創作規則、參考資料與歷史備份。2026-09-01 已由 [Google Drive 專案資料夾](https://drive.google.com/drive/folders/1U_SBT-cHPmT-hfcjHpr6NPMg31HUmaMd) 完整匯入，文件統一轉為 UTF-8 Markdown，方便逐行修改、審閱與建立 Pull Request。

## 目錄

- `AGENTS.md`：所有代理與協作者修改小說前必須遵守的現行創作規則（權威來源）。
- `.grok/skills/`：施工操作層（Draft Capsule、起稿、QA、11 同步、備份）。不創造 Canon。
- `tools/`、`evals/`、`.github/workflows/`：機械掃描、迴歸與 CI；工具命中須人工依 `AGENTS.md` 判定。
- `10_現行創作資料/`：正文、設定總表、章節大綱與工程治理資料。
- `90_參考資料/`：角色或創作參考資料。
- `governance/`：change-manifest、Capsule 輸出與 CI evidence（JSON 不進 git）。
- `99_備份/`：歷史快照；含 Compiler 誘餌檔，絕不可當施工來源。
- `00A_設定歷史修改紀錄｜Changelog.md`：現行設定與規則變更紀錄。

## 修改與 PR

1. 先閱讀根目錄的 `AGENTS.md`。
2. 從 `main` 建立新分支，例如 `rewrite/p05`、`canon/linoir-age`。
3. 只修改本次工作涉及的 Markdown 檔案；若影響 Canon、規則或歷史紀錄，一併同步相關檔案。
4. 提交後推送分支並建立 Pull Request。
5. 更新 `governance/change-manifest.yaml`。提交前跑 `py -3 evals/ci_suite.py`（Windows）或等 GitHub Actions 產 SHA-bound evidence。PATTERN RISK 只提供候選。

現行內容應在 `10_現行創作資料/` 修改；`99_備份/` 用於追溯，不作為日常編輯入口。
