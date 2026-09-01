---
name: novel-canon-pack
description: Assemble a minimal Draft Capsule and Context Pack from current authority files without loading full QA tables. Use before writing or rewriting a chapter, when the user asks for a capsule, context pack, 讀取範圍, or Governance 施工前準備.
when-to-use: Draft Capsule, Context Pack, 起稿前, 讀哪些設定, 壓縮治理資料
argument-hint: "[chapter-or-scene]"
---

# novel-canon-pack

把治理資料壓成主筆能用的最小包。不創造 Canon。

## 必跑 Compiler

不要靠模型自己「想起」該讀哪些檔。先跑：

```text
py -3 tools/compile_context.py --target P08 --check-only
```

產出必須含 machine-readable provenance，例如 `KNOW-013 ← 11 / Knowledge / K013`。`99_備份/`、`00A`、`90_參考資料/` 出現在 loaded_paths 就是失敗。

## Authority

服從 Compiler 載入的現行檔，不要把內容抄進本 skill：

1. 作者本輪明確指示
2. `AGENTS.md`
3. `10_現行創作資料/01-08_小說設定總表｜角色・關係・劇情資料.md`
4. `10_現行創作資料/09_序章～第一篇章節大綱｜第二版.md`
5. `10_現行創作資料/11_小說工程治理總表｜Knowledge・State・QA・TBD.md`（後台；主筆只帶走 Capsule）
6. `10_現行創作資料/小說正文第三版.md`

禁止當施工來源：`99_備份/`、00A、舊 07／08／09、原型報告，除非作者明確要求回顧。

## 步驟

1. 讀 `governance/change-manifest.yaml` 的 `revision_level`。R4 沒有作者決定且 `canon_change: true` 就停。
2. 跑 Compiler，保留 provenance。
3. Capsule 欄位以 11 的 DRAFT CAPSULE TEMPLATE 為準。若已能看出整章流水線，刪欄位。
4. TBD 標籤不得進正文。

## 交付

Capsule ＋ provenance ＋正文路徑。不要交完整 State Diff／Dependency／Acceptance Tests。
