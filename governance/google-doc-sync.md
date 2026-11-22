# Google 文件自動單向同步設定指南（Issue #40）

本專案遵循 `AGENTS.md` §2 單向發布原則：
- **唯一施工稿**：`10_現行創作資料/小說正文第三版.md`（GitHub `main` 分支）。
- **Google 文件（含原生分頁 Tabs）**：僅作為發布輸出，不得反向覆寫儲存庫權威。
- **目標文件 ID**：`1Qg63ffCy3DlLNpmr1mBz-_yjHDgRBY-QbFxRNI5jOt4`

---

## 一、自動化運作方式

當以下檔案合併進 `main`（或從 GitHub Actions 手動觸發 `Sync Draft to Google Doc`）時，[`.github/workflows/sync-google-doc.yml`](../.github/workflows/sync-google-doc.yml) 會執行 [`tools/sync_google_doc.py`](../tools/sync_google_doc.py)：

1. 依 `# 第N章｜章名` 自動切分正文各章節與段落，拒絕空章或重複章號。
2. 透過加密 HTTPS POST 將章節 JSON 傳送至綁定在目標 Google 文件內的 **Google Apps Script Web App**（[`tools/google_apps_script_sync.gs`](../tools/google_apps_script_sync.gs)）。
3. 接收端驗證 `SYNC_SECRET` 後，呼叫內建 `Google Docs API` 更新各原生分頁標題與內文；若有新章自動新增分頁，若多出舊分頁則改標為 `[預留] 第N章（PLANNED）` 而不直接刪除。

> 本機已登入 `gdocs` CLI 時，亦可手動執行 `py -3 tools/sync_google_doc.py --mode gdocs` 直接由本機同步。

---

## 二、作者一次性設定步驟（約 3 分鐘，免建立 GCP Service Account）

### 步驟 1：在 Google 文件綁定 Apps Script
1. 開啟目標 Google 文件：`https://docs.google.com/document/d/1Qg63ffCy3DlLNpmr1mBz-_yjHDgRBY-QbFxRNI5jOt4/edit`
2. 點擊上方選單 **擴充功能 → Apps Script**。
3. 將本儲存庫 [`tools/google_apps_script_sync.gs`](../tools/google_apps_script_sync.gs) 的內容完整貼入編輯器（取代原本的 `myFunction`）並存檔。

### 步驟 2：開啟進階 Google Docs 服務與密碼屬性
1. 在 Apps Script 左側欄點擊 **服務 `+`** → 選取 **Google Docs API**（識別碼保持預設 `Docs`）→ 按 **新增**。
2. 點擊左側齒輪 **專案設定** → 拉到最下方 **指令碼屬性 → 新增指令碼屬性**：
   - 屬性名稱：`SYNC_SECRET`
   - 值：自行設定一組長隨機字串（例如 `2026novel-...`）並暫記下來。

### 步驟 3：部署為 Web App
1. 點擊右上角 **部署 → 新增部署** → 齒輪選取 **網頁應用程式**。
2. 設定：
   - **執行身分**：`我（文件擁有者）`
   - **誰可以存取**：`所有人`（實際請求須通過 `SYNC_SECRET` 才執行寫入）
3. 按 **部署** 並完成 Google 帳號授權確認後，複製產生的 **網頁應用程式網址（Web app URL）**。

### 步驟 4：將網址與密鑰存入 GitHub Secrets
1. 前往 GitHub 儲存庫 **Settings → Secrets and variables → Actions → New repository secret**。
2. 新增兩筆 Repository Secrets：
   - `GDOC_WEBHOOK_URL`：步驟 3 複製的 Web App URL
   - `GDOC_WEBHOOK_SECRET`：步驟 2 設定的 `SYNC_SECRET` 字串

設定完成後，可到 GitHub **Actions → Sync Draft to Google Doc → Run workflow** 按一次手動觸發驗證自動同步。
