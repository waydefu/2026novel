# evals

迴歸層。驗證「工具有沒有照權威邊界工作」，不是驗證小說好不好看。

版本：見 `VERSION`。

```text
py -3 evals/run_evals.py
py -3 evals/ci_suite.py
```

必須包含：故意破壞的 negative controls、R-level、Compiler 不載入備份誘餌、drift、recovery drill、現行正文 hard-gate。
