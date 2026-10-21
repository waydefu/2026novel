# ADR｜決議紀錄（Architecture/Author Decision Records）

本資料夾記錄**會改變規則或方向**的決議。純行文、錯字、格式修正不進 ADR（見 AGENTS.md §16.4）。

## 為什麼要 ADR

規則檔會膨脹。ADR 讓「當初為什麼這樣決定」留下可追溯的證據，避免日後有人推翻它卻不知道代價。借用 ADR（architecture-decision-record）與 MADR 的 Status 生命週期。

## Status 生命週期

| Status | 意義 | 後續動作 |
|---|---|---|
| `proposed` | 已提出，未決 | 不得依賴該決議施工 |
| `accepted` | 已採用 | 可依賴；後續修改需新 ADR |
| `deprecated` | 已廢棄 | 不再依賴，保留紀錄 |
| `superseded` | 被新 ADR 取代 | 在 `superseded_by` 指向新 ADR |

## Template

```markdown
# ADR｜<標題>

STATUS：proposed | accepted | deprecated | superseded
DATE：YYYY-MM-DD
DECIDERS：<誰決定>

## Context

<為什麼現在要決定；相關事實與限制；引用可查證來源>

## Decision

<決定了什麼。用祈使句寫成規則。>

## Consequences

<因此必須新增／改動哪些檔案、流程或閘門；有哪些成本>

## Alternatives considered

<被拒絕的方案與拒絕理由>

## Verification

<如何確認已正確落地；對應的工具或測試>
```

## 索引

| ADR | 標題 | Status | 日期 |
|---|---|---|---|
| [0001](0001-canon-direction.md) | 設定與正文的權威方向 | accepted | 2026-10-22 |
