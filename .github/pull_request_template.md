## 本次變更

<!-- 簡述修改的章節、角色、設定或規則。 -->

## Revision manifest

對應 `governance/change-manifest.yaml`：

- revision_level：
- target：
- canon_change：
- governance_sync：
- backup_ref：

## 連動文件

<!-- 列出一併同步的正文、設定、規則、Changelog 或大綱；沒有則填「無」。 -->

## 授權範圍

- 作者本輪授權的原話或連結：
- 本次修改的受保護檔案（見 `governance/trust-and-authorization.md` §3）：無／逐一列出

## 交付證據

- 改動檔案與理由：
- 實際執行的指令與 exit code：
- 未執行或未通過的檢查：
- 可能的副作用（What could break）：
- 回退方式（`backup_ref` 或 commit）：
- 聲明：AI 自己的摘要不是 CI 證據，以 `gate-proven` 與 evals 的實際結果為準。

## 提交前確認

- [ ] 已閱讀並遵守根目錄 `AGENTS.md`（權威來源；`.agents/skills/` 只負責流程）
- [ ] 已更新 `governance/change-manifest.yaml`，且 R-level 與實際改動檔一致
- [ ] 已核對 Canon、角色人設與時間線
- [ ] 已檢查「又／再次／依舊／果然」等詞的前文資訊前提
- [ ] 已檢查 AI 高頻套式、機械式動作／感受與 POV 越界
- [ ] 已維持自然繁體中文、既定敘事比例與輕小說語感
- [ ] 已冷讀修改範圍並檢查標題、段落、引號與分頁標記
- [ ] 若改正文：hard-gate／evals 由 CI 綁定本次 SHA；PATTERN RISK 僅作候選
- [ ] 若變更影響規則或設定，已同步相關文件與 Changelog
- [ ] 受保護檔案的修改都對應本輪作者授權，且未放寬任何檢查門檻
