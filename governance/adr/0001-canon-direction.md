# ADR｜設定與正文的權威方向（Canon Direction）

STATUS：accepted
DATE：2026-10-22
DECIDERS：專案所有者（授權「四件事你來決定」）

## Context

兩種主流做法互相衝突：

- **工程式（本專案原本的做法）**：Canon 在上游（01–08 設定總表），正文不得反向改寫 Canon。優點是 AI 不會擅自把寫出來的東西升格成設定；缺點是正文寫久了會與設定脫節，而且「改設定」的成本被推高。
- **產業式（Sudowrite 等 AI 輔助工具）**：「大綱會漂移，你寫出來的那個場景才是正典」。優點是設定永遠反映實際文本；缺點是若無管制，AI 會用一句話把設定改掉。

社群另提供分層做法（llm-knowledge C1–C5）：C1 設定檔與 C2 正文事實都是 binding，C3 草稿只是 provisional，C5 衝突阻擋升級。

## Decision

採**方向性雙軌**：

1. **正文寫下即既存事實。** 已被接受章節中的事實不得被設定檔或新稿矛盾；衝突由 `tools/canon_contract.py` + `governance/canon-contracts.json` 阻擋。
2. **正文不得自行升格 Canon。** 文本中出現的新設定（規則、動機、制度、身分）只是正文事實，不得自動寫回 01–08；升格須作者明確決定，走 R4。
3. **設定修改只能追認或走 retcon。** 設定檔與既有正文衝突時，選項只有 (a) 追認：把正文事實寫進設定；(b) retcon：新增一筆明示的 retcon 紀錄，把舊設定標 `superseded`。不得直接改寫既有 Canon 條目。
4. **衝突升級即阻擋。** 兩來源互斥時標為 `CONTRADICTION`，該項相關章節不得進入正文層（對應 11 §08 的 TBD 阻擋機制）。

## Consequences

- 需要新增 `governance/canon-contracts.json`：把「後續章實際依賴的既存事實」寫成可執行的契約（角色年齡、物品持有者、時間跨度、已確立副作用、PLOT RESET 邊界）。契約只驗證已鎖定事實，不是全設定表的快照。
- `tools/canon_contract.py` 成為阻擋式閘門，失敗即 CI 紅。
- 設定檔未來若要跟正文同步，屬 R4（需作者決定）＋附帶 ADR 條目。
- 契約本身是 append-only：新增用新 id，被取代的標 `status: superseded` 並指向新 id。

## Alternatives considered

- **純工程式（維持原狀）**：拒絕。代價是正文與設定脫節只能靠人記。
- **純產業式（正文優先）**：拒絕。AI 輔助下會讓未經作者確認的設定滲入 Canon。
- **只靠人工冷讀**：拒絕。ConStory-Bench 等研究顯示一致性錯誤集中在事實與時間維度、且偏在敘事中段，人工容易漏。

## Verification

`py -3 tools/canon_contract.py` 於現行正文回報 0 violations；`evals/run_evals.py` 含契約違規樣本（必須紅）與合規樣本（必須綠）。
