# 研究彙整｜2026-10-22 治理與中文去 AI 味

STATUS：REFERENCE ONLY（無 Canon 權力；只記錄外部研究的可用部分與裁決）

本檔是兩份外部研究的摘要與裁決紀錄。原始出處見文末。研究的細節不在此重複，只保留「對本專案產生改變的部分」。

## A. 治理研究（可用部分）

### A1. 借用的做法與出處

| 做法 | 出處 | 本專案落點 |
|---|---|---|
| ADR 的 Status 生命週期（proposed／accepted／superseded） | architecture-decision-record、MADR | `governance/adr/`（ADR-0001 已建立） |
| Definition of Done（跨工作項目的共同完成定義） | Atlassian | `governance/definition-of-done.md`（R0–R4 各自定義） |
| Contract by example（只驗 consumer 實際依賴的條目） | Pact | `governance/canon-contracts.json`（10 條契約） |
| 「你寫出來的那個場景才是正典」 | Sudowrite blog | ADR-0001 的方向性雙軌 |
| Canon 分層 C1–C5、append-only、retcon | llm-knowledge NOVEL.md | 契約 `status` 欄與 supersede 機制 |
| 角色／事件可查詢物件（Event／Backstory／Arc） | Aeon Timeline | 11 的 State Diff／Dependency（既有） |
| 分級 CI（error 阻擋／warning 顯示） | Vale + GitLab | 既有 HARD GATE／PATTERN RISK 分層，本次再補契約與體量閘門 |
| 單一事實來源產生各工具規則檔 | Ripple RuleSync | `governance/agent-rules-source.md` → `.cursor/rules/`、`.github/copilot-instructions.md`、`CLAUDE.md` |
| 可 pin 的詞表雜湊（證明尺子沒變） | defluff | `governance/lexicon.lock` |
| 逐章投稿須保留三件套 | 晋江 AI 輔助寫作公告 | `governance/evidence-policy.md` |
| 編輯提修訂標記、作者執行；代改須議定 | 晋江出版常見問題 | R1–R4 分層既有對應；新增作者直覺通道（見下） |
| 敘事順序 vs 時間順序 | Aeon Timeline | 契約 `scope.from` 支援章序鏈 |
| 一致性錯誤偏在事實／時間維度與敘事中段 | ConStory-Bench | 契約與複核比重偏中段章節 |

### A2. 風險與反模式（採納為約束）

| 反模式 | 證據 | 本專案的處置 |
|---|---|---|
| 規則文件過厚降低成功率 | Anthropic（>200 行、150–200 指令上限）；刪 80% AGENTS.md 一文（原始 ETH 論文未查證） | AGENTS.md 壓到 ≤200 行；`tools/check_rule_budget.py` 阻擋 |
| 規則被移出後遺失 | — | `governance/rule-budget.json` 的 hoisted_rules 登記制；缺指針＝違規 |
| 多代理協調下降 30%；檔案不重疊仍有 47.3% 衝突 | CooperBench、NP-Bench、MergeGym | 事前切分不相交範圍；先計畫後發問；合併後重跑整合檢查 |
| 規格膨脹（420→873 行） | spec-kit Issue #860 | 每季稽核規則；失效規則退場 |
| 證據制淪為形式（CI 綠但審查無效） | GitOps 失效模式 | 證據必須綁定可讀 diff／行號；`governance/provenance/` 記「保留理由」與「未驗證」 |
| 「編輯不能不帶腦子，只依循流程工作」 | 台灣資深編輯座談（Openbook） | 工具只給候選；冷讀與作者直覺通道保留 |
| canon 凍結敘事 | Sudowrite 使用者回饋 | ADR-0001 允許追認與 retcon；P08 可拆章 |
| 大綱是草稿不是契約 | LitMemo、巴哈姆特作者經驗 | 09 只鎖節點；章內路線開放 |

### A3. 未查證（不當事實用）

Master Novel 官方文件；「刪 80% AGENTS.md」的 ETH 原始論文；台灣編輯工會資源；「編劇人／雜糅」部落格；番茄與晋江的部分數字口徑；閱文／番茄／晋江 的編輯內部會審 SOP。

## B. skills 生態研究（可用部分）

### B1. 格式規格

| 項目 | 內容 | 出處 |
|---|---|---|
| 標準結構 | `skill-name/SKILL.md` ＋ `scripts/` `references/` `assets/`（選填） | agentskills.io/specification |
| 必填 frontmatter | `name`（1–64 字元、僅 `a-z0-9-`、不可連續連字號、須與父目錄同名）、`description`（1–1024 字元，須同時寫「做什麼」與「何時用」） | 同上 |
| 選填 frontmatter | `license`、`compatibility`、`metadata`、`allowed-tools` | 同上 |
| 漸進式揭露 | metadata（~100 tokens）→ SKILL.md（<500 行）→ references／scripts（用到才讀） | Anthropic 工程文 |
| 打包陷阱 | 標準外欄位在 claude.ai 打包時是**硬錯誤**，不是忽略 | Anthropic skill-creator 實測 |
| Cursor | `.cursor/rules/**/*.mdc`；frontmatter `description`／`alwaysApply`／`globs`；`.md` 副檔名會被忽略 | Cursor docs |
| Copilot | `.github/copilot-instructions.md`；路徑專屬用 `.github/instructions/*.instructions.md`（`applyTo` 必填） | GitHub docs |
| Codex | 逐層 `AGENTS.md`／`AGENTS.override.md`，越近越優先，合併上限 32 KiB | OpenAI docs |
| AGENTS.md | 開放標準，Linux Foundation 託管；離被改檔最近者勝 | agents.md |

→ **本專案既有 5 個 skill 的 `when-to-use`／`argument-hint`／`paths` 屬 Claude Code 擴充欄位**，若要跨工具通用（Cursor／Codex／OpenCode）或打包上 claude.ai，會報硬錯誤。本次改寫一律只用標準 6 欄，Claude 專屬行為改寫在內文「執行邊界」段落。

### B2. 中文去 AI 味社群資源（可用部分）

| 資源 | 網址 | 可借 |
|---|---|---|
| speak-human-tw（繁體，38 種痕跡，含誤殺邊界） | https://github.com/Raymondhou0917/speak-human-tw | 規則骨架 |
| zh-tw-humanizer（繁體台灣，60 特徵＋157 兩岸用語＋31 案例 eval） | https://github.com/acchuang/zh-tw-humanizer | 在地化層 |
| qu-ai-wei（簡體，逐條附證據等級） | https://github.com/LifelongLazyLearner/qu-ai-wei | 證據分級制度（**明文不處理繁體**） |
| lieflat-less-ai-tone（唯一有語料統計者） | https://github.com/larashero3-dotcom/lieflat-less-ai-tone | R 值與「不作為改寫理由」表 |
| blader/humanizer（英文，26 條編號模式） | https://github.com/blader/humanizer | 失效模式命名與 before/after 格式 |
| oh-story-claudecode（13 skill，含 story-deslop） | https://github.com/zenstory-ai/oh-story-claudecode | 三層去味（表達／用筆／故事）、改稿前自動備份 |
| aeopress/novel-skills（novel-bible／audit／plan） | https://github.com/aeopress/novel-skills | 活設定集、稽核維度、章前 memo |
| chinese-novelist-skill（記憶／懸念鉤子／自動校驗） | https://github.com/PenglongHuang/chinese-novelist-skill | 三件套設計 |
| chinese-longnovel-skill（伏筆追蹤／一致性審查） | https://github.com/xiaofeng-928/chinese-longnovel-skill | 伏筆台帳與狀態回證 |
| Agent Skills 標準與 `skills-ref` 驗證器 | https://github.com/agentskills/agentskills | 格式校驗 |

繁體中文在這個領域是空白市場（多數中文 skill 明文只做簡體），因此本專案自建的繁體規則庫有實際價值。

### B3. 社群結論衝突與本專案裁決

| 衝突點 | 兩方說法 | 裁決 |
|---|---|---|
| 段落長度 CV | lieflat 實測 R=0.94 不成立 vs aeopress 當警示 | **僅提示，不設限** |
| 正文「首先／其次／最後」 | lieflat 無差異 vs speak-human-tw／qu-ai-wei 要處理 | **只在硬拆三點且三點長度幾乎相等時才動** |
| 破折號 | 通用門檻，模型間極差 40 倍 | **改用本專案自有正負樣本量測**（`tools/style_profile.py`） |
| 比喻是否該刪 | 多數 humanizer 勸刪 vs 語料實測人類用更多 | **不刪；只處理理想化擬人喻體** |

### B4. 可借的驗證標準

`shuorenhua` 的發布門檻：資訊硬失敗＝0、**正常文本誤改率 < 10%**、正向樣本多數有可見收益。本專案已在 `evals/run_evals.py` 落實正／負樣本與鎖檔檢查。

## C. 出處

治理面：ADR（github.com/architecture-decision-record）、MADR（github.com/adr/madr）、Atlassian DoD、Pact docs、GitHub spec-kit（spec-driven.md、constitution-template.md、Issue #860、Issue #75）、Martin Fowler〈Understanding SDD〉、IBM GitOps、terrateam GitOps failure modes、Vale、agents.md、Cursor docs、GitHub Copilot docs、OpenAI Codex docs、Anthropic equipping agents、CooperBench（arXiv 2601.13295）、NP-Bench（arXiv 2610.07261）、MergeGym（arXiv 2610.04779）、AgenticFlict（ACM AIware'26）、ConStory-Bench（arXiv 2603.05890）、defluff、slop-guard、textlint、Openbook 台灣編輯座談、晋江 AI 輔助寫作公告、閱文／番茄／晋江 官方文件、巴哈姆特作者實作、LitMemo、RAID benchmark、Liang et al. 偵測器偏誤研究。

skills／中文去 AI 味面：agentskills.io、Anthropic skills、ComposioHQ/awesome-claude-skills、speak-human-tw、zh-tw-humanizer、qu-ai-wei、lieflat-less-ai-tone、blader/humanizer、oh-story-claudecode、novel-skills、chinese-novelist-skill、chinese-longnovel-skill、shuorenhua、stop-slop、avoid-ai-writing、human-writing、renwei、CCL 2023 中文對照語料研究、ACL 2024 Threads of Subtlety、EMNLP 2024 Syntactic Templates、中文維基「AI生成文的特徵」、英文維基「Signs of AI writing」。
