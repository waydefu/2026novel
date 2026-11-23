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
3. 接收端驗證 `SYNC_SECRET` 並限制目標只可為指定 Google 文件，使用同一批 Google Docs API 請求更新原生分頁的**標題與正文**；若有新章自動新增分頁，若多出舊分頁則改標為 `[預留] 第N章（PLANNED）` 而不直接刪除。
4. 接收端重新讀取所有受影響分頁，逐章比對**分頁 ID、標題與全文文字**，全部一致才回傳 `verified: true`；呼叫端再次確認章數、文件 ID 與來源 SHA。任一步失敗（包含改名、重新讀取或驗證失敗）都使同步工作顯示失敗，不能只靠 `ok: true` 或 GitHub Actions 綠燈宣稱 Google 文件已同步。
5. GitHub Actions 會序列化發布作業，較舊的 `main` 提交不再執行同步；未設定 Secrets 不再以成功略過。

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


---

## 三、更新接收器與驗收（修正分頁名稱不一致）

2026-11-24 審查發現：原 Webhook 能成功更新七章內文，但第二、第三、第七分頁仍保留舊標題。原因是舊接收器把改名失敗降為警告，又未讀回比對，造成「部分成功卻顯示成功」。

**本次修復需要同時更新 GitHub 程式與 Google Apps Script 部署；只合併 GitHub PR 不會自動替換已部署的 Web App。**

1. 在綁定目標文件的 Apps Script 編輯器中，更新為最新版 `tools/google_apps_script_sync.gs`。
2. 到 **部署 → 管理部署作業 → 編輯（鉛筆）→ 版本：新增版本 → 部署**。務必使用既有 Web App 部署，避免更換 URL；保留原 `SYNC_SECRET`，不要把密鑰寫進 GitHub 或對話。
3. 合併修正 PR 後，於 GitHub **Actions → Sync Draft to Google Doc → Run workflow** 執行正式同步（`dry_run=false`）。
4. 查看 `OK webhook-sync-verified chapters=N` 與成功的 Actions 結果，再開啟文件核對分頁名稱。若接收器仍是舊版、改名失敗、正文不一致或 Secret 缺失，工作應變紅，屬於**未完成同步**；請勿宣稱已成功。
5. `evals/google_doc_sync_receiver.test.cjs` 是使用模擬 Docs API 的測試，不會寫入真實 Google 文件。CI 綠燈僅證明程式契約與模擬案例通過，**不代表已部署或已完成實際文件驗收**。

## 四、已知共享權限風險（作者決定暫緩）

- **2026-11-24 實測：** 目標 Google 文件設為「知道連結的任何人＝編輯者（writer）」，連結不會透過搜尋公開列出（`allowFileDiscovery: false`）；另有特定共同編輯者。
- **風險：** 持有連結的人可能修改或覆寫發布中的小說內容；此模式也不適合把綁定文件的 Apps Script 與存放密鑰的指令碼屬性視為只對作者可控的環境。
- **作者決定：**「權限暫時不用管，記錄即可」。本次 PR **不變更分享連結、不移除共同編輯者、不輪替密鑰**，不把權限調整當作 CI 或同步修復的前置條件；待作者另行授權再處理。
