# evidence

GitHub Actions 寫入 JSON。欄位：

- `head_sha`：PR 分支頭（或 push 的 commit）
- `base_sha`：比較基準
- `tested_sha`：實際跑測的 commit（`pull_request` 上通常是 merge candidate，**不是** head）
- `tested_ref_type`：`pull_request_merge_candidate` / `push_head` / `local`
- `commit`：等於 `tested_sha`（舊欄位別名）

artifact 名稱用 **head SHA**，檔名用 **tested SHA**。不要拿別次綠燈當這次通過。
