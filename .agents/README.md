# 操作層｜Skills・Tools・Evals・CI

本目錄與根目錄 `tools/`、`evals/`、`.github/workflows/` 組成施工操作層。

權威不在這裡。

```
現有 Governance（AGENTS.md／01–06／09／11／作者指示）
      ↓
保持 authority
      ↓
.agents/skills/（把操作流程工具化）
      ↓
tools / evals / CI（機械掃描、迴歸、門檻）
```

## 權威邊界

- 規則、Canon、Knowledge、TBD、章級目的仍以 `AGENTS.md`、`10_現行創作資料/` 為準。
- Skills 只寫「先讀什麼、用哪個模式、產出什麼、何時停手」。
- 工具命中是候選，不是判決。HARD GATE 由人依 `AGENTS.md` §11 判定；PATTERN RISK 不得因關鍵字零命中而宣告通過。
- Skills 與工具若和更高權威衝突，服從更高權威，並回報衝突，不得在操作層自行折衷。

## Skills（來源唯一）

來源在 `.agents/skills/`（Agent Skills 規格；OpenCode、Codex、agents.md 生態都能發現）。
其他工具的路徑由 `tools/sync_skills.py` 產生，**不可手動複製**：

```text
py -3 tools/sync_skills.py --check                 # 驗證來源規格 + 檢查鏡像是否同步
py -3 tools/sync_skills.py --mirror .claude/skills  # 為 Claude Code 產生鏡像
py -3 tools/sync_skills.py --clean                  # 移除所有鏡像（切換工具前執行）
```

同一個工作目錄只留**一個**鏡像：OpenCode 會同時掃描 `.opencode/`、`.claude/`、`.agents/`，
同名 skill 會重複載入。

| Skill | 何時用 | 不負責 |
| --- | --- | --- |
| `novel-canon-pack` | 起稿前跑 Context Compiler，產出可追溯 Capsule | 不寫字 |
| `novel-draft-mode` | 寫或改正文；服從 change-manifest 的 R-level | 不驗收、不改 Canon |
| `novel-prose-audit` | 文風與去 AI 味問題；預設只標不改 | 不動情節與事實 |
| `novel-qa-mode` | 整章驗收、冷讀、Hard Gate 判定 | 不寫字 |
| `novel-canon-contract` | 發現與分類 Canon 矛盾、retcon 流程 | 不自行改設定 |
| `novel-state-sync` | QA 通過後才同步 11，並跑 drift | 不創造 Canon |
| `novel-backup` | R2 以上先備份；restore 後必須再跑 eval | 不當施工來源 |
| `novel-provenance` | 產出逐章溯源紀錄 | 不驗收品質 |
| `novel-decision` | 方向性決議（ADR）與尺子變更留痕 | 不處理日常行文 |

路由細則見 `governance/skill-routing.md`。

## Gate-Proven Baseline

達標條件：skills 通過規格驗證 ＋ R-level enforcement ＋ context provenance ＋ evals 回歸 ＋ path-aware hard-gate ＋ commit-bound CI evidence ＋ recovery drill。

## 不放進 Skills 的東西

- 完整 Fail Code 表、完整 State Diff、完整 Dependency Graph、完整 Acceptance Tests
- 角色 Bible 全文、世界規則全文
- 舊 07／08／09 或 `99_備份/` 的劇情
