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

## 獨立執行原則（Pass 3 上下文隔離）

- 為避免主筆在同一對話窗內對自己剛寫出的句子產生辯護慣性，**Pass 3 修稿審校應交由獨立的新對話上下文（或新開一個子代理）執行**，只帶入待審正文、凍結事實帳本與該場角色 Voice 卡。

## 步驟（Pass 3 逐句手術六關）

1. **判定情境與力度**：只標問題／直接改寫／只改節奏／只做冷讀。沒有明確指示時，預設**只標不改**。
2. **凍結事實帳本**：人、事、時、地、數字、因果、引語、專名、角色年齡與物品持有者。
3. **跑掃描**：

```text
py -3 tools/prose_lexicon.py       # 詞庫候選
py -3 tools/prose_lexicon.py --not-evidence   # 不可當依據者
py -3 tools/prose_rhythm.py        # 節奏：只作冷讀定位
py -3 tools/style_profile.py       # 量測，含「非判據」標記
```

4. **人工執行六項 Pass 3 手術**（命中與問題皆依實證判讀，成立 → 改；不成立 → 保留並寫理由；需作者決定 → 標 NEEDS AUTHOR）：
   - **情緒直述與動作是否重複**：檢查「動作＋多餘心理結論」是否真的重複，能刪再刪；必要時可直接寫情緒或心理。FACS 動作庫只是備用素材，不應把所有情緒詞改成肌肉動作。
   - **一秒濾鏡詞檢測法（Deep POV）**：掃描「看見、聽見、感覺到、意識到、注意到、心想」。嘗試刪掉該動詞——若後面具體畫面仍在，通常是濾鏡詞，優先刪去直呈畫面；若只剩抽象結論，屬於 Telling 須重寫。**三種例外刻意保留**：資訊差發現（「他看著她藏信」）、創傷抽離／高燒失實感、不可靠誤判（「他以為對方在笑」）。
   - **結構與詞庫去 AI 味**：優先處理 `ai-flavor-evidence.md` 成立項（「不是 X 而是 Y」、冒號空轉、段首評論、「一絲／一抹＋神態」、不由得／不禁）；嚴禁把「幾乎／似乎」或句長均勻度拿來機械洗稿。
   - **對話降拋光與聲線檢查**：把像辯論或審計員問答的完整對白，調整成帶潛台詞的短句、停頓、打斷或遞物代答；對照 `11` §03 `VOICE-WORDS` 避免多角撞聲。
   - **動作與感官的必要性**：刪除確實拖慢節奏且沒有作用的監控式小動作；不設「每個動作都必須三選一」或每段感官種類上限。
   - **結尾適切性檢查**：判斷場末／章末是否有無來源的哲理或替讀者劃重點；有問題才修。允許用對白、決定、直接情緒或動作收尾，不規定每章停在物件。
5. **最小改稿與複掃比對**：不動事件、因果、關係狀態；複跑工具並比對事實帳本確認零漂移。
6. **交付報告**（格式見下）。

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
