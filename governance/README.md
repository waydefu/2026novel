# change-manifest

每個會改治理／正文／設定的 PR 都要更新本檔。CI 用它做 R0–R4 機械檢查。

```yaml
revision_level: R2
target: chapter-08
canon_change: false
governance_sync: true
backup_ref: 99_備份/01_正文備份/小說正文第三版｜第八章前備份｜2026-09-01.md
```

- R1 改 01–06 → FAIL
- R2+ 沒有 `backup_ref` → FAIL
- 只改 11、不改正文 → FAIL
- 修改 `99_備份` 既有檔 → FAIL
- 01–06 必須 `revision_level: R4` 且 `canon_change: true`

Path 必須保留 `.github` / `.grok` / `.gitignore`，並用 `git -c core.quotePath=false diff --name-only -z` 解析 Unicode 檔名。不要為了迎合壞輸入而放寬 R0。
