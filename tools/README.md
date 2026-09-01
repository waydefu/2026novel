# tools

機械掃描層。不創造 Canon，不覆寫 `AGENTS.md`。

本機 Windows 用 `py -3`；CI 用 `python`。

| 指令 | 作用 | CI |
| --- | --- | --- |
| `scan_hard_gate.py` | 只對現行正文：TBD、P-0N 章名、姓名拼寫 | 命中則失敗；備份／00A／11 豁免 |
| `scan_pattern_risk.py` | 前情詞、套式、診療用語候選 | 只報告 |
| `count_chapter.py --chapter N` | 章內漢字字數 | 不設門檻 |
| `compile_context.py --target P08` | Context Compiler＋provenance；拒絕 `99_備份` | 失敗則紅 |
| `check_revision_gate.py` | R0–R4 manifest vs 變更檔 | 失敗則紅 |
| `check_derived_drift.py` | 11 與正文／09 明顯不一致 | 失敗則紅 |
| `write_evidence.py` | SHA-bound evidence JSON | CI artifact |

PATTERN RISK 的命中必須人工判定。不要把本目錄的正則當成 Fail Code 表。
