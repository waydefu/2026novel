# 操作層｜Skills・Tools・Evals・CI

本目錄與根目錄 `tools/`、`evals/`、`.github/workflows/` 組成施工操作層。

權威不在這裡。

```
現有 Governance（AGENTS.md／01–06／09／11／作者指示）
      ↓
保持 authority
      ↓
.grok/skills/（把操作流程工具化）
      ↓
tools / evals / CI（機械掃描、迴歸、門檻）
```

## 權威邊界

- 規則、Canon、Knowledge、TBD、章級目的仍以 `AGENTS.md`、`10_現行創作資料/` 為準。
- Skills 只寫「先讀什麼、用哪個模式、產出什麼、何時停手」。
- 工具命中是候選，不是判決。HARD GATE 由人依 `AGENTS.md` §13 判定；PATTERN RISK 不得因關鍵字零命中而宣告通過。
- Skills 與工具若和更高權威衝突，服從更高權威，並回報衝突，不得在操作層自行折衷。

## Skills

五個 skill 維持不變，不再新增。要把這五條路跑硬，而不是再切碎片。

| Skill | 何時用 |
| --- | --- |
| `novel-canon-pack` | 起稿前跑 Context Compiler，產出可追溯 Capsule |
| `novel-draft-mode` | 寫或改正文；服從 change-manifest 的 R-level |
| `novel-qa-mode` | 寫後驗收、冷讀、Hard Gate |
| `novel-state-sync` | QA 通過後才同步 11，並跑 drift |
| `novel-backup` | R2 以上先備份；restore 後必須再跑 eval |

## Gate-Proven Baseline

達標條件：5 skills stable ＋ R-level enforcement ＋ context provenance ＋ ≥20 evals ＋ path-aware hard-gate ＋ commit-bound CI evidence ＋ recovery drill。

## 不放進 Skills 的東西

- 完整 Fail Code 表、完整 State Diff、完整 Dependency Graph、完整 Acceptance Tests
- 角色 Bible 全文、世界規則全文
- 舊 07／08／09 或 `99_備份/` 的劇情
