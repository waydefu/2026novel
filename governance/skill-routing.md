# Skill 路由與部署

STATUS：ACTIVE｜更新：2026-10-22

## 為什麼需要這份

九個 skill 覆蓋了整條工作流，但名稱相近容易同時命中。`name` 與 `description` 是代理決定是否載入 skill 的主要訊號，因此路由規則必須寫在**各 skill 的 description 與本檔**，不能只放在腦中。

## 路由表

| 使用者說什麼 | 先用哪個 | 明確不做什麼 |
|---|---|---|
| 「幫我寫第八章」「重寫這段」 | `novel-draft-mode` | 不驗收、不改 Canon、不改設定 |
| 「起稿前要讀什麼」「給我 capsule」 | `novel-canon-pack` | 不寫字 |
| 「這章太 AI」「太碎」「太空」「去 AI 味」 | `novel-prose-audit` | **預設只標不改**；不動情節與事實 |
| 「驗收這章」「QA」「冷讀」「有沒有破規」 | `novel-qa-mode` | 不寫字；可呼叫文風流程 |
| 「設定衝突」「年齡對不上」「東西不該在這」 | `novel-canon-contract` | 不自行改設定；只分類矛盾 |
| 「同步 11」「更新 State」 | `novel-state-sync` | 不創造 Canon、不升格 TBD |
| 「先備份」「快照」 | `novel-backup` | 不當施工來源 |
| 「留個紀錄」「溯源」 | `novel-provenance` | 不驗收品質 |
| 「這條規則要改」「決定方向」 | `novel-decision` | 不處理日常行文 |

### 重疊時的裁決順序

1. **文風問題**（太 AI、太碎、太空）→ 先 `novel-prose-audit`（只標），再由 `novel-qa-mode` 整章驗收。
2. **設定衝突** → 先 `novel-canon-contract` 判定是「正文寫錯」「設定落後」還是「需要 retcon」；只有需要新決定時才交 `novel-decision`。
3. **動筆前** → `novel-canon-pack` → `novel-draft-mode`；動筆後 `novel-qa-mode` →（狀態有變）`novel-state-sync` → `novel-provenance`。
4. 任何情況下，**作者最新指示優先**；skill 之間衝突時以 `AGENTS.md` 為準。

## 部署

- 唯一來源：`.agents/skills/<name>/SKILL.md`。
- 其他工具的路徑（`.claude/skills/`、`.opencode/skills/`、`.grok/skills/`）由 `tools/sync_skills.py` 產生，**不可手動編輯**。
- 同一工作目錄只留一個鏡像：OpenCode 同時掃描三條路徑，同名 skill 會重複載入。
- 規格符合性由 `tools/validate_skills.py` 檢查（name 與目錄同名、`^[a-z0-9]+(-[a-z0-9]+)*$`、description 1–1024、只允許 name/description/license/compatibility/metadata/allowed-tools、metadata 必須是字串→字串映射）。

## 規格紅線（實測）

| 項目 | 規則 | 違反後果 |
|---|---|---|
| 額外 top-level frontmatter | 不允許 | 上傳 claude.ai／Skills API **硬錯誤**（不是忽略） |
| `metadata` 值型別 | 必須是字串 | 嚴格驗證器可拒絕 |
| `name` 與目錄名 | 必須相同 | 載入器可能找不到 |
| `name` 格式 | 小寫、單一連字號、1–64 字元 | 觸發不了 |

## 觸發測試（尚未實作）

skill 是否真的會在正確情境被選中，需要行為測試而不是文件檢查：同一組提示分別餵給有 skill 與無 skill 的代理，比較是否選中正確 skill、是否依序呼叫工具、是否越權改 Canon。目前 `evals/run_evals.py` 只驗格式與工具行為，**尚未涵蓋端對端代理行為**——這是已知缺口，補上之前不要宣稱「流程保證會執行」。
