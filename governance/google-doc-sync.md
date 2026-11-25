# Google 文件自動單向同步設定指南（Issue #40）

本專案遵循 `AGENTS.md` §2 單向發布原則：
- **唯一施工稿**：`10_現行創作資料/小說正文第三版.md`（GitHub `main` 分支）。
- **Google 文件（含原生分頁 Tabs）**：僅作為發布輸出，不得反向覆寫儲存庫權威。
- **目標文件 ID**：`1Qg63ffCy3DlLNpmr1mBz-_yjHDgRBY-QbFxRNI5jOt4`

---

## 一、自動化運作方式

當以下檔案合併進 `main`（或從 GitHub Actions 手動觸發 `Sync Draft to Google Doc`）時，[`.github/workflows/sync-google-doc.yml`](../.github/workflows/sync-google-doc.yml) 會執行 [`tools/sync_google_doc.py`](../tools/sync_google_doc.py)：

1. 依 `# 第N章｜章名` 自動切分正文各章節與段落，拒絕空章、重複或不連續章號。
2. 透過加密 HTTPS POST 將章節 JSON 傳送至綁定在目標 Google 文件內的 **Google Apps Script Web App**（[`tools/google_apps_script_sync.gs`](../tools/google_apps_script_sync.gs)）。
3. 接收端驗證 `SYNC_SECRET` 並限制目標只可為指定 Google 文件，使用同一批 Google Docs API 請求更新原生分頁的**標題與正文**；若有新章自動新增分頁，若多出舊分頁則改標為 `[預留] 第N章（PLANNED）` 而不直接刪除。
4. 接收端重新讀取所有受影響分頁，逐章比對**分頁 ID、標題與全文文字**，全部一致才回傳 `verified: true`；呼叫端再次確認章數、文件 ID 與來源 SHA。任一步失敗（包含改名、重新讀取或驗證失敗）都使同步工作顯示失敗，不能只靠 `ok: true` 或 GitHub Actions 綠燈宣稱 Google 文件已同步。
5. GitHub Actions 使用 `queue: max` 排隊，**每一個排隊的執行在發布前都先抓取最新 `main`**（包括只有治理檔變動的提交）；因此不會因「觸發時的 SHA 不再是最新」而直接跳過最後一次可用的同步。發送端使用重新取得的來源 SHA，而非舊事件 SHA。未設定 Secrets 不再以成功略過。
6. 發布端讀取 Google 文件 `revisionId` 並在更新中使用 `writeControl.requiredRevisionId`；共同編輯者若在讀取後修改，請求必須失敗而不能用過期索引覆寫。**原文已相同的分頁不送任何正文變更**；其他分頁只修改必要的文字範圍，不再整章刪除重建，減少註解／格式受影響的範圍。

> 優先使用 revision-guarded webhook。本機 CLI 的整頁替換沒有相同的修訂鎖，可能破壞註解錨點；僅限備份或隔離副本，且必須明確加上 `--mode gdocs --allow-destructive-replace`。它只驗證標題，不能當作正式發布成功證據。

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

- **註解與共同編輯限制：** 不變的七章正文可以完全跳過寫入，保留既有批註的位置；**若文字本身真的變更，落在被修改字元上的註解錨點仍可能受影響**，Google Docs API 無法對所有註解保證原位置。正式重同步前應保留可回復的 Google 文件版本或備份。


## 五、Google Docs API 已知分頁改名相容性問題（待實機確認）

Google 官方 Issue Tracker [561660144](https://issuetracker.google.com/issues/561660144) 記載：某些已刪除原始 `t.0` 分頁的文件，呼叫 `updateDocumentTabProperties` 可能得到 HTTP 500。**目前目標文件所見八個分頁 ID 均非 `t.0`，因此存在相容性風險，但此 PR 尚未對線上接收器做真正的改名測試，不能宣稱已確認發生相同錯誤。**

新版程式遇到此類錯誤會**讓整次同步標記失敗**，不會把正文已更新、標題仍舊的情況當成成功。若重新部署後改名仍失敗，可在 Google 文件介面手動將舊分頁標題與目前正文一致，再重新執行正式同步驗收；若日後章名再改，仍可能需要人工處理。無作者另行決定，不重建或更換既有 Google 文件，也不刪除分頁以迴避 API 問題。

## 六、2026-11-24 可靠性強化（PR #50）

在 PR #49 合併後，2026-11-24 實測 Google Actions [45223235356](https://github.com/waydefu/2026novel/actions/runs/45223235356) 出現 `Webhook response is not verified`；正式文件七章正文仍與 `main` 一致，但 Ch2／Ch3／Ch7 及預留 Ch8 分頁標題尚有舊名。**程式升級不等於已部署；線上驗收仍屬待辦。**

本輪修改：新增 `requiredRevisionId` 避免共同編輯時覆寫、將未變更分頁設為 no-op、對變更內容只更新最小差異字串；若需建立分頁，仍是「先建立再讀取新修訂」的兩階段流程，已在兩個 API 呼叫中各自校驗 revision，**不能宣稱所有步驟為單一原子交易**。GitHub 同步工作佇列改用 `queue: max`，每次從 `origin/main` 取得目前正文，再送出其真實 SHA，解決非正文提交造成的跳過風險。新增模擬「共同編輯造成版本衝突」、「內容未變更完全不寫入」與「微小字串差異不全章重建」的測試。

**上線限制：** 在 Google Apps Script Web App 升版前，GitHub 端仍會拒絕舊接收器不帶 `verified` 的回應，不能透過重跑工作冒充同步成功。Google Docs API 的舊分頁改名 500 問題仍需實際驗證；若觸發，先保留正文與既有分頁，必要時在 Google 文件介面人工改名，不能為了顯示全綠而刪除文件或註解。正式部署操作需保留分頁、註解及原分享權限。

## 七、PR #51 稽核修補

- 寫入前核對各分頁 UTF-16 結構索引；只容許起始分節符，中間分節符或索引異常拒絕寫入。
- 建立分頁後使用 batchUpdate 回應的新 revision，再讀取文件；若共同編輯者在兩階段之間修改文件，拒絕後續正文寫入。建立分頁已發生，不宣稱兩階段原子。
- 手動 dry-run 保留所選分支，正式寫入才取 main；queue: max 最多排隊 100 個執行，非無限容量。
- 新版接收器、Mock 與程式碼測試不等於線上部署。先以另行核准的副本進行 E2E，不在正式文件上試錯。

## 八、2026-11-25 隔離副本驗證

正式文件七章逐段文字（忽略空行及段落首尾空白）與 #52 後 main 一致，四個原生分頁名稱仍過時。已建立[非正式同步測試副本](https://docs.google.com/document/d/1O_3hsMaUdBidHx0xHYvga03RSbLkPptivSqbipyo1Ts/edit)，以目前 revisionId 提交四個 `updateDocumentTabProperties`，連接器回傳內部錯誤；讀回八個分頁名稱及各段文字與樣式，均保持原樣。此結果只能證明副本改名未成功，不能推定 Google HTTP 500 或認證失效，也不是 Apps Script 實機測試。正式文件、原分享權限與 Secrets 未修改；仍需作者在 Apps Script 管理部署中更新既有 Web App 版本，再進行隔離 E2E 與正式同步。
