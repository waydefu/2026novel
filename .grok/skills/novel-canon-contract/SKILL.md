---
name: novel-canon-contract
description: Check the live draft against machine-readable canon contracts, and record retcons when canon must change. Use when 設定與正文衝突、既有事實可能被改掉、需要 retcon、或使用者要求 驗契約／retcon／追認. Contract violations block the merge; they are never resolved by rewriting the contract to fit the prose.
license: MIT
compatibility: 需要 Python 3.12+ 執行 tools/canon_contract.py
metadata:
  version: "1.0.0"
  when_to_use: "canon 契約, retcon, 追認, 設定衝突, 既存事實"
  argument_hint: "[contract-id]"
allowed-tools: Read Grep Glob Edit Bash
---

# novel-canon-contract

方向（ADR-0001）：**設定是 provider，已寫正文是 consumer**。已寫正文的既存事實不得被矛盾；正文也不得自行升格 Canon。

## 跑檢查

```text
py -3 tools/canon_contract.py            # 阻擋式：違規即失敗
py -3 tools/canon_contract.py --json     # 機器可讀輸出
```

契約在 `governance/canon-contracts.json`（append-only）。

## 契約結構

```json
{
  "id": "CC-0XX",
  "status": "active | superseded",
  "title": "一句話",
  "scope": { "all": true } | { "chapters": ["第五章｜…"] } | { "from": "第五章｜…" },
  "require": ["必須出現的樣式"],
  "forbid": ["不得出現的樣式"],
  "rationale": "為什麼需要這條"
}
```

- `require`：該範圍內必須命中，否則視為既存事實被刪掉。
- `forbid`：該範圍內不得命中。
- `scope.from`：從某章往後生效（適合年齡、時間跨度這類會隨章節變化的約束）。

## 違規時的三種解法（依序）

1. **正文寫錯了** → 改正文。這是最常見情況。
2. **正文對、設定落後** → 追認：更新設定檔（R4，需作者決定），契約不動。
3. **設定本來就錯、要改寫既有事實** → retcon：新增一筆契約（`superseded_by` 指向新 id）或在 `governance/adr/` 記錄決議；舊契約標 `status: superseded`，**不得直接改寫既有條目**。

絕對不可為了讓檢查變綠而修改契約內容。契約是尺子，改尺子要走 `novel-decision`。

## 新增契約的時機

- 新章寫下作者已確認的既存事實（年齡、物品持有者、已確立副作用、時間跨度）。
- 讀者會依賴、但設定檔還沒記的事實（可加 `require`）。
- 只驗證「後續章實際依賴」的條目，不要把整份設定表快照成契約。

## 交付

回報：違規清單、每條的解法（改正文／追認／retcon）、是否需要作者決定。改正文時同步更新 11（`novel-state-sync`）。
