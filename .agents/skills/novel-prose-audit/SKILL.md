---
name: novel-prose-audit
description: Audit and de-AI-ify Traditional-Chinese prose in this novel with corpus-backed evidence tiers. Use when 去 AI 味、說人話、這段好 AI、語感不對、句太碎、太空、太平均, or when a chapter needs rhythm and Chinese AI-flavor review. Machine hits are candidates only; metaphors, rhetorical questions, parallelism and passive voice are NOT evidence of AI authorship and must not be removed for that reason.
license: MIT
compatibility: 需要 Python 3.12+ 執行 tools/prose_lexicon.py、tools/prose_rhythm.py、tools/style_profile.py
metadata:
  version: "1.0.0"
  when_to_use: "去 AI 味, 說人話, 語感, 碎句, 太空, 太平均, 反 AI, prose audit"
  argument_hint: "[chapter|file]"
  evidence_doc: "governance/ai-flavor-evidence.md"
allowed-tools: Read Grep Glob Edit Write Bash
---

# novel-prose-audit

繁體中文去 AI 味校訂。**本 skill 不做 AI 偵測繞過**，只做「哪裡讀起來像模板」的可證據化判讀。

## 三層防護

1. 機械掃描結果一律視為**待人工判讀的線索**，不得單獨作為改寫依據；零命中不等於通過。
2. 判定依據分三層：機器可算（詞形、密度）／機器只能算字面形態（對舉、比喻、限定詞）／機器算不出（是否刻意、是否文學效果）。
3. 輸出必須把「機械線索（嫌疑）」與「語意判讀與處置」分區，且「保留理由」必填。

## 證據分級（重要）

`governance/ai-flavor-evidence.md` 記錄了哪些中文特徵真的判別 AI 味。以下**不成立**，不得作為刪改理由：

- 句長均勻度（R=0.87）、段長均勻度（R=0.94）
- 比喻（R=0.42，人類是 AI 的 2.4 倍）、獨立成段的比喻（8 倍）
- 設問句（R=0.05，人類是 AI 的 17 倍）
- 句內排比（R=0.61）、被動句（R=0.70）、動詞名詞化（R=0.52）

**成立**且優先處理：冒號空轉句引列表（R=9.4）、理想化擬人喻體（R=7.3）、段首零回指評論（R=4.4）、「不是 X 而是 Y」（R=3.4）、起手式（R=3.2）、序數詞小標題（R=3.1）、概括覆蓋具體（R=0.35）。

## 步驟

1. 判定情境與力度：只標問題／直接改寫／只改節奏／只做冷讀。沒有明確指示時，預設**只標不改**。
2. 凍結事實帳本：人、事、時、地、數字、因果、引語、專名、角色年齡與物品持有者。
3. 跑掃描：

```text
py -3 tools/prose_lexicon.py       # 詞庫候選
py -3 tools/prose_lexicon.py --not-evidence   # 不可當依據者
py -3 tools/prose_rhythm.py        # 節奏：只作冷讀定位
py -3 tools/style_profile.py       # 量測，含「非判據」標記
```

4. 逐條人工判讀：成立 → 改；不成立 → 保留並寫理由；需作者決定 → 標 NEEDS AUTHOR。
5. 改稿只在最小範圍內進行，不動事件、因果、關係狀態。
6. 複掃並比對事實帳本，確認零漂移。
7. 交付報告（格式見下）。

## 輸出格式

```markdown
## 機械線索（嫌疑，未經語意判讀）
| 位置 | 指標 | 數值 | 規則 ID |

## 語意判讀與處置
| 位置 | 原句 | 規則 ID | 判定 | 處置 | 理由 |

## 保留理由（命中但語意成立）
- §3 L12：刻意短句是莉諾兒呼吸不穩的表現，保留。

## 需作者確認
- …
```

## Fail 條件

- 零命中不等於通過，仍要完成語意判讀並寫明。
- 命中但語意成立者不得靜默略過。
- 改稿後數字／日期／專名／代詞有增減 → 不交付。
- 涉及情節、因果、動機、角色選擇 → 不在本 skill 範圍，交 `novel-draft-mode`／`novel-canon-contract`。
- 若正文的既存事實會被改動 → 交 `novel-canon-contract` 判斷（改正文／追認／retcon）。
