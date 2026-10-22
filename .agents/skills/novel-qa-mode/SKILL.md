---
name: novel-qa-mode
description: Post-draft QA for live novel chapters. Runs hard-gate tools, human-judges pattern risk, judges rhythm and Chinese AI-flavor candidates with corpus-backed evidence tiers, syncs nothing unless asked, and finishes with a cold read. Use after writing, when reviewing a chapter, 驗收, 冷讀, Fail Code, or 反 AI. Machine hits are candidates, never verdicts.
license: MIT
compatibility: 需要 Python 3.12+ 執行 tools/ 掃描器（選用）
metadata:
  version: "2.0.0"
  when_to_use: "QA MODE, 驗收, 冷讀, Hard Gate, Pattern Risk, 反 AI, 去 AI 味"
  argument_hint: "[chapter]"
  paths: "10_現行創作資料/小說正文第三版.md"
  opencode/slash: "true"
allowed-tools: Read Grep Glob Edit Write Bash
---

# novel-qa-mode

寫後驗收。工具找候選；人依 `AGENTS.md` 判定。

## 順序

1. 重新讀修後範圍，不要只看 diff。
2. 跑機械掃描（候選，不是自動判決）：

```text
py -3 tools/scan_hard_gate.py      # 阻擋式
py -3 tools/canon_contract.py      # 阻擋式
py -3 tools/scan_pattern_risk.py   # 候選
py -3 tools/prose_lexicon.py       # 候選（--not-evidence 看不可當依據者）
py -3 tools/prose_rhythm.py        # 候選：只作冷讀定位
py -3 tools/style_profile.py       # 量測：非判據項目標「非判據」
py -3 tools/count_chapter.py --chapter N
py -3 tools/check_derived_drift.py
py -3 evals/run_evals.py
```

3. HARD GATE：Canon、POV 越界、Knowledge、資訊前提、術語、明確 OOC、格式。成立就改。
4. PATTERN RISK：只有形成模式、角色同質、或真的變難讀才 Fail。不得為了消滅關鍵字把文字洗成動作報告。
5. 需要同步 11 時才跑 `novel-state-sync`。純行文不改 Knowledge／State／Dependency。
6. 自由冷讀：不問有沒有守規則，只問哪裡怪、假、卡、像模板。
7. 規則全過但不好讀＝未完成。

## 機械掃描不能證明的事

- 關鍵字零命中 ≠ 通過人味
- 工具沒抓到 POV 越界 ≠ 沒有越界
- 句長均勻度、比喻、設問、排比、被動句**不是** AI 判別指標（見 `governance/ai-flavor-evidence.md`）
- evals 綠燈 ≠ 場景有生命

## Windows 主控台編碼

本專案的工具輸出是繁體中文。Windows 主控台預設 cp950 會把 `・` 之類的字元打成亂碼，
甚至讓工具直接崩潰。兩種可靠作法：

```text
# 1) 直接跑，但先設編碼
$env:PYTHONIOENCODING='utf-8'; py -3 tools/xxx.py

# 2) 需要拿到正確輸出時，用 python 收字串再寫檔
py -3 -c "import subprocess,sys; sys.stdout.reconfigure(encoding='utf-8'); print(subprocess.run([sys.executable,'tools/xxx.py'],capture_output=True,text=True,encoding='utf-8',errors='replace').stdout)"
```

不要把亂碼輸出當成工具結果；看不懂就先換上面的作法。

## 判讀紀律

每個命中三選一，不得靜默略過：

- 成立 → 改。
- 不成立 → 保留，並寫下保留理由。
- 需要作者決定 → 標 NEEDS AUTHOR，交回作者。

## 交付摘要

修改範圍、主要修正模式、章長、Canon／TBD 狀態、跑過哪些檢查、哪些未驗證。正文裡不要出現這些標籤。
