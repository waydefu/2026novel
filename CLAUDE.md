<!-- generated from governance/agent-rules-source.md by tools/sync_agent_rules.py — do not edit by hand -->

# 《2026西幻小說》代理規則（精簡版）

## 唯一施工稿

`10_現行創作資料/小說正文第三版.md`。其他正文檔（第二版、99_備份）只可回顧，禁止施工。

## 權威順序

1. 作者本輪明確指示
2. `AGENTS.md`（根規則）
3. `10_現行創作資料/01-08_小說設定總表｜角色・關係・劇情資料.md`（人物／關係 Canon）
4. `10_現行創作資料/09_序章～第一篇章節大綱｜第二版.md`（章綱）
5. `10_現行創作資料/11_小說工程治理總表｜Knowledge・State・QA・TBD.md`（衍生狀態，不創造 Canon）
6. `10_現行創作資料/小說正文第三版.md`

## 硬性禁止

- 不得從舊 07／08／09、舊正文、備份、模型常識補設定（CANON-01）。
- 不得把 TBD、規則說明、審稿標籤寫進正文。
- 不得讓正文自行升格 Canon；不得改變已寫正文的既存事實而不走 retcon。
- 不得在沒有作者決定時自行決定 TBD、動機、制度、法律身分、宗教位階、魔法規則。
- 不得為了消滅風險詞把文字洗成動作報告。

## 兩種模式

- DRAFT MODE：READ → 壓縮成最小 Draft Capsule → 起稿。先讓場景成立，再修句子。
- QA MODE：重讀 → Hard Gate → 人工判定 Pattern Risk → 自由冷讀。工具命中只是候選。

## 修改流程

1. 讀 `governance/change-manifest.yaml` 的 `revision_level`（R0–R4）。
2. R2 以上先備份，正文快照放 `99_備份/01_正文備份/`。
3. 改正文後同步 11 的 Knowledge／State／Dependency（`governance_sync: true`）。
4. 跑 `py -3 evals/ci_suite.py`；PR 需通過 `gate-proven`。

## 交付要求

只交付修後正文與驗證摘要。寫明修改範圍、修正模式、章長、Canon／TBD 狀態、跑過哪些檢查、哪些未驗證。
