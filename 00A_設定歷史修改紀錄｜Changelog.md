# 00A｜SETTING CHANGELOG

## 《2026西幻小說》設定歷史修改紀錄

STATUS：ACTIVE / HISTORY ONLY

AI AUTHORITY：NONE

ROOT AUTHORITY：00_創作規則＋01–06 現行設定總表

TIMEZONE：Asia/Taipei

本文件只記錄設定與文件治理的歷史變更，不是現行 Canon 來源。任何衝突一律回到作者最新指示、00 根規則與 01–06 現行設定判定。

# 1｜使用規則

1.1 每次對人物、關係、世界設定、主線治理、AI 讀取規則或文件結構做實質修改，都新增一筆 Change Entry。

1.2 不可為了讓歷史看起來乾淨而改寫舊紀錄。舊紀錄若有錯，新增 CORRECTION 條目修正。

1.3 Changelog 只描述「曾經怎麼改」，不能用來覆寫現行設定。

1.4 TBD／暫定／事件原型轉為正式 Canon 時必須記錄；反向作廢亦同。

1.5 純錯字或不影響語意的排版微調可合併記錄，不必逐字建立條目。

1.6 所有時間使用 Asia/Taipei；同日多筆以 Change ID 排序。

# 2｜Change Entry Schema

CHANGE ID：CHG-YYYY-MM-DD-###

DATE：YYYY-MM-DD HH:mm +08:00

TYPE：GOVERNANCE / CANON / CLARIFICATION / DEPRECATION / FORMAT / FIX / CORRECTION

SCOPE：受影響文件／分頁／設定項

BEFORE：變更前狀態

AFTER：變更後狀態

REASON：為什麼修改

AUTHORITY：作者指示／00 規則／一致性修正／其他可追溯來源

COMPATIBILITY：BREAKING / NON-BREAKING / DOCUMENT-ONLY

VALIDATION：如何確認已正確落地

# 3｜歷史紀錄

## CHG-2026-09-02-001

## DATE：2026-09-02 00:00 +08:00

## TYPE：GOVERNANCE / FIX

## SCOPE：`tools/check_revision_gate.py` path parser、`write_evidence.py` 三 SHA、evals 0.2.1、Governance CI artifact 命名

## BEFORE：`posix()` 用 `lstrip("./")` 把 `.github`／`.grok`／`.gitignore` 剝成 `github`／`grok`／`gitignore`；`git diff --name-only` 預設 quote 非 ASCII 路徑，Revision Gate 在 GitHub Actions 假陽性失敗。Evidence 只存 `github.sha`，PR 上被當成 merge candidate 而與 head SHA 對不上。

## AFTER：path 只去掉開頭 `./`、保留 dotfile；git 用 `core.quotePath=false` 與 `-z`，並能 unescape C-quote。Evidence 改為 `base_sha`／`head_sha`／`tested_sha`／`tested_ref_type`。R0 規則未放寬。evals 增加 `.github`／`.grok`／中文檔名 integration cases。

## REASON：修 GitHub 實戰抓到的 path transport bug，不改閘門寬度。

## AUTHORITY：作者指示只修 path parser、三 SHA evidence、CI 全綠後 main ruleset。

## COMPATIBILITY：NON-BREAKING / DOCUMENT-ONLY

## VALIDATION：`posix(".github/...")` 仍以 `.github` 開頭；quoted `00A_…Changelog.md` 能分類為 ops；`evals/run_evals.py` 通過。

## CHG-2026-09-01-005

## DATE：2026-09-01 23:30 +08:00

## TYPE：GOVERNANCE / FORMAT

## SCOPE：tools／evals／CI、governance/change-manifest、`.grok/skills/` 五條流程（不新增 skill）、00 16.10、99_備份 Compiler 誘餌檔

## BEFORE：Governance Runtime v0.1：五個 skill 與 6 個 scanner evals；hard-gate 可能誤傷 00A／11／備份；R0–R4 沒有機械 enforcement；Capsule 不可追溯；沒有 backup lure、drift、commit-bound evidence 或 recovery drill。

## AFTER：Gate-Proven Baseline。hard-gate 改為 path-aware（只 enforce 現行正文）；R-level 讀 change-manifest；`compile_context.py` 產出 provenance 且拒絕 `99_備份`；evals 擴成含 negative controls 的迴歸；CI 寫 SHA-bound evidence artifact；fixture recovery drill 證明 backup→mutate FAIL→restore PASS。`99_備份/00_非現行｜Compiler誘餌｜請勿施工.md` 只作負向控制，無 Canon 權威。

## REASON：把現有五條路跑硬，形成可證明的閉環，而不是再加 skill。

## AUTHORITY：作者指示補齊 negative controls、R-level gate、provenance、commit-bound evidence、recovery drill；先不 commit、不加 skill。

## COMPATIBILITY：NON-BREAKING / DOCUMENT-ONLY

## VALIDATION：`py -3 evals/run_evals.py` 案例數 ≥20 且全過；Compiler 輸出不含 `LURE_TOKEN_SHADOW_PRINCESS_NOT_CANON`。

## CHG-2026-09-01-004

## DATE：2026-09-01 22:57 +08:00

## TYPE：GOVERNANCE / FORMAT

## SCOPE：`.grok/skills/`、`tools/`、`evals/`、`.github/workflows/governance-ci.yml`、00 根規則導航 16.10、README

## BEFORE：Governance 2.0 已把規則、Canon 與狀態留在 00／01–06／09／11，但施工步驟仍靠代理每次重讀長文，沒有專案內 skill、機械掃描或 CI。

## AFTER：權威來源不變。新增操作層：`.grok/skills/` 只編碼 Capsule／DRAFT／QA／11 同步／備份步驟；`tools/` 掃 HARD GATE 與 PATTERN RISK 候選；`evals/` 迴歸掃描器本身；CI 對現行正文跑 hard-gate，PATTERN RISK 只報告。00 增補 [OPS] 導航與 16.10，明確 skills／工具不具 Canon 權威。

## REASON：把操作流程工具化，同時避免把治理表或 Fail Code 複製進 skill 造成第二套權威。

## AUTHORITY：作者指示「現有 Governance → 保持 authority → .grok/skills/ → 把操作流程工具化 → tools / evals / CI」。

## COMPATIBILITY：NON-BREAKING / DOCUMENT-ONLY

## VALIDATION：skills 內容指向現行檔而不複製規則表；`python evals/run_evals.py` 通過；現行正文 hard-gate 通過。

## CHG-2026-09-01-003

## DATE：2026-09-01 02:16 +08:00

## TYPE：GOVERNANCE / CORRECTION / FIX / FORMAT

## SCOPE：00 根規則、01–08 設定總表｜04 莉諾兒、09-P06～P08、11_小說工程治理總表、小說正文第三版第六～第七章、00A 與治理備份

## BEFORE：專案已有 Knowledge／State／Dependency／Acceptance Tests 等工程治理，但主筆起稿仍容易直接接觸完整治理表；STYLE／AI 類規則也容易被當成單句硬性 Fail。09-P06／P07 仍以日期、限制解除與安全訊號排列心理進展，P08 則把數月到數年的共同生活壓在單一章節框架內。這種治理雖能保住 Canon，卻會讓正文出現 State Diff 逐項履約、角色即時自我分析、信任單向增加與場景過度有效率等 AI 痕跡。施工收尾時另發生一次工具事故：對原現行 11 使用過短的全域句號替換，誤刪文件內大量「。」；事故檔隨即停止作為施工來源。

## AFTER：Governance 2.0 正式落地。00 將 DRAFT MODE 與 QA MODE 分離，新增 Draft Capsule、Narrative Firewall、Hard Gate／Pattern Risk 分級、非線性人類反應與 Over-compliance 檢查；主筆起稿只載入必要 POV／Knowledge／2～4 個 Hard Canon 邊界／Voice／大致終點，完整 Acceptance Tests、State Diff 與 Dependency 留到寫後 QA。09 升為 v2.2-DRAFT-01：P06／P07 改為 Hard Outcome＋Relationship Boundary＋Creative Freedom，不再用日期與信任節點逐格履約；P08 改為 ARC BLOCK，可依實際場景拆成多章。04 莉諾兒 Canon 與 00 10.8 同步改為「事件事實不等於信任進度條」，允許理性、安全判斷、身體習慣與情緒不同步。正文第六、七章依小型 Draft Capsule 重寫並重新 QA：時間主要透過治療、吃飯、走動、陌生腳步、日常小事與反覆反應呈現；真正走出正門後仍可能睡得更差；取得其他去處後選擇「我先留在這裡」並保留其他選項，不把暫留寫成完全信任。QA 另移除一處未經 Canon 確認的「安置地可能有影貓族」推測，改為「目前沒有確認」。原 11 事故檔（ID：1YL-yw7djnfOn433bBSqWCpwV9iEPQkputcucbOaMBH0）已移入 99_備份／03_治理紀錄備份封存；以治理 2.0 前完整備份恢復出新的現行 11（ID：1fE-MzMVNUJ1CjYcu_CQWvKGFdD-PLILlP3dkJiJNZPM），重新套用 Governance 2.0 並同步 Ch6／Ch7 的 Knowledge、Reader Knowledge、State Diff 與 Dependency。00 導航已改指向新現行 11。

## REASON：保留工程治理對 Canon、POV、Knowledge 與跨章因果的保護力，同時切斷「治理表直接變成正文」造成的過度合規與 AI 味；並以可驗證的備份復原處理工具事故，不人工猜補被誤刪的 391 個句號。

## AUTHORITY：作者本輪明確指示「繼續完成」；依現行 00 的反 AI、No-Guess、版本治理與備份規則執行。

## COMPATIBILITY：NON-BREAKING / GOVERNANCE / PROSE / DOCUMENT-ONLY

## VALIDATION：00 已可找到新現行 11 URL 與「不得把安全證據排成信任進度條」條文；11 已驗證存在 DRAFT CAPSULE TEMPLATE、Acceptance Tests｜GOVERNANCE 2.0、VOICE DIFFERENTIATION TEST、更新後 Ch6／Ch7 OUTCOME、查爾曼單獨 KNOWS 暫留決定、Reader Knowledge 新工作邊界與 D010「Ch7 暫留 ≠ 工作」；09 已驗證 VERSION＝v2.2-DRAFT-01 與 P08 ARC BLOCK。正文第六／七章與設定總表已在本輪重新核對；未新增法律制度、屠村真相、轉生機制、學院正式身分或未確認種族安置答案。11 重新套用前備份保留於 02_設定與規則備份，00A 收尾前備份保留於 03_治理紀錄備份。

## CHG-2026-09-01-002

## DATE：2026-09-01 01:07 +08:00

## TYPE：GOVERNANCE / CORRECTION / FORMAT / FIX

## SCOPE：11_小說工程治理總表、00_創作規則 10.8、正文第一～第七章驗證基線

## BEFORE：11 已建立 Knowledge／State／QA／TBD 等工程治理內容，但全部集中在單一預設分頁，後續 Agent 不易按任務精準載入；其中 Ch3～Ch7 的 State／Knowledge 仍標 PROSE-RECHECK。00 10.8 另殘留「莉諾兒約十歲」與「沒有賣身契」式舊描述，和已鎖定的「莉諾兒九歲、亞德里安約十歲」及正式法律／契約仍為 TBD 不一致。

## AFTER：11 重整為 9 個 Google Docs 原生文件分頁：00 使用說明與權威、01 Revision Levels、02 Acceptance Tests、03 Voice Fingerprints、04 Knowledge Ledger、05 Reader Knowledge、06 State Diff、07 Dependency Graph、08 TBD・Unknown Register。重新讀取現行正文第一～第七章後，Ch1～Ch7 全部改為 VERIFIED 基線，並依現行正文重建／校準 Knowledge、Reader Knowledge、State Diff 與跨章 HARD／SOFT Dependency。00 10.8 同步修正為莉諾兒九歲、亞德里安約十歲，改以吊墜未被奪、家人／村民紀錄、持續尋找倖存者、限制逐步解除與實際其他去處支撐自主暫留；工作與正式身分維持後續另行自願成立，不再預設特定契約制度。

## REASON：讓後續長篇施工能以 relevant memory 精準讀取工程資料，移除已過期的 PROSE-RECHECK 與年齡／制度殘留，同時確保任何尚未定稿的真相或制度繼續保持 TBD，不由模型自行補完。

## AUTHORITY：作者明確要求直接開始補齊工程治理層，且有問題立即問、不得猜；現行 00、01–06、09、正文第一～第七章，以及 CHG-2026-08-31-001 的年齡 Canon。

## COMPATIBILITY：NON-BREAKING / CORRECTION / DOCUMENT-ONLY / GOVERNANCE

## VALIDATION：11 修改前已建立單一治理里程碑快照；00 與 00A 亦各建立一份本輪收斂前治理快照。正文第一～第七章均已重新讀取；11 的 Knowledge／Reader Knowledge／State／Dependency 只記現行可驗證事實或明確 [PLANNED]，13 項未決內容仍保持 OPEN TBD；00 10.8 精確替換 1 處，未新增任何法律、屠村真相、轉生機制或學院制度答案。

## CHG-2026-09-01-001

## DATE：2026-09-01 00:50 +08:00

## TYPE：GOVERNANCE / FORMAT

## SCOPE：00 根規則、10_現行創作資料、新增 11_小說工程治理總表

## BEFORE：專案已有 00 的權威順序、場景卡、Hard Fail、Final QA、TBD 原則與備份治理，也有 01–06 人物／關係 Canon、09 新主線與現行正文，但「誰知道什麼、讀者知道什麼、每章前後狀態差、後文硬依賴、可修改層級、五人聲音壓縮指紋與跨文件 TBD」仍分散在多份來源中，缺少可持續更新的單一操作型狀態層。

## AFTER：新增《11_小說工程治理總表｜Knowledge・State・QA・TBD》並放入 10_現行創作資料。11 明定自身只為衍生操作層、不得創造或覆寫 Canon；建立 L0–L7 來源用途、R0–R4 Revision Level、章級 Acceptance Tests、五人 Voice Fingerprint、Knowledge Ledger、Reader Knowledge Ledger、Ch1–Ch7 State Diff、Scene／Chapter Dependency Graph、13 項現行 TBD／Unknown Register、更新協議與 P08 施工 handoff。00 導航與寫章節路由同步加入 11；Ch3–Ch7 未在本輪逐句重讀之項目明確標 PROSE-RECHECK，不以 09 規劃冒充正文驗證。

## REASON：降低長篇施工時的資訊漂移與模型偷補空白風險，讓新章／重寫任務能先取得明確的 Knowledge、State、Dependency、TBD 與修改邊界，同時避免再拆出多份高度相似文件。

## AUTHORITY：作者要求「開始補齊」工程治理層，並明確要求有問題不得猜；現行 00、01–06、09 與正文作為來源。

## COMPATIBILITY：NON-BREAKING / DOCUMENT-ONLY / GOVERNANCE

## VALIDATION：建立修改前 00 與 00A 單一里程碑備份；11 已重新讀取確認內容寫入，並已移入 10_現行創作資料；00 新導航與新章施工路由各替換 1 處成功。所有未決真相／制度均保持 TBD，沒有自行升格 Canon。

## CHG-2026-08-31-002

## DATE：2026-08-31 22:33 +08:00

## TYPE：GOVERNANCE / DEPRECATION / FORMAT

## SCOPE：專案根目錄、99_備份／01_正文備份、02_設定與規則備份

## BEFORE：近期規則複檢與 Canon 同步又產生多份只差一次局部修改的完整快照；專案根目錄散落 3 份 2026-08-30「移除莉諾兒幼年持刀前」備份，01_正文備份累積至 8 份，02_設定與規則備份累積至 9 份，人工與 AI 都容易把中間快照誤認成仍需保留的施工來源。

## AFTER：恢復里程碑保留制。專案根目錄只保留 00、00A、10_現行創作資料、90_參考資料、99_備份。01_正文備份只留 4 個節點：P01-P04 整體修正前、P05 全面重寫前、章節命名與文件分頁重排前、2026-08-31 AI 味全項複檢前。02_設定與規則備份只留 4 個節點：01-08 作者決策同步前、09 第五～第七章重構前、01-08 莉諾兒年齡同步前、09 莉諾兒年齡同步前。03_治理紀錄備份維持不動。共永久刪除 12 份已被後續完整快照或歷史紀錄覆蓋的中間備份。

## REASON：降低相似文件噪音，讓現行來源與真正有回滾價值的里程碑一眼可辨，避免後續 Agent 誤讀舊快照。

## AUTHORITY：作者 2026-08-31 明確指示「太多類似文件，清理一下」＋既有里程碑備份治理原則。

## COMPATIBILITY：DOCUMENT-ONLY / GOVERNANCE

## VALIDATION：專案根目錄重新列出後僅 5 個入口；10_現行創作資料仍只有正文、01-08 設定總表、09 大綱三份現行文件；99_備份／01 與／02 各剩 4 份里程碑快照，現行文件 ID 均未改變。

## CHG-2026-08-31-001

## DATE：2026-08-31 21:50 +08:00

## TYPE：CANON / CORRECTION / CLARIFICATION

## SCOPE：01–08 設定總表｜04 莉諾兒；09_序章～第一篇章節大綱｜第二版 P05

## BEFORE：莉諾兒初遇年齡仍寫成「約九至十歲」，09-P05 另標示精確年齡不在本章鎖死，與作者後續反覆以「九歲小女孩」明確校正 P05 角色反應的指示不一致。

## AFTER：莉諾兒與亞德里安初遇時固定為九歲；亞德里安約十歲。04 角色 Bible 的 EVENT POLICY 與初遇段落、09-P05 均改為九歲，不再保留九至十歲浮動值。

## REASON：作者最新明確指示已把莉諾兒的初遇年齡定為九歲；精確年齡會直接影響創傷反應、台詞與思考成熟度，不能繼續留成模糊區間。

## AUTHORITY：作者最新明確指示。

## COMPATIBILITY：BREAKING / CANON / CLARIFICATION

## VALIDATION：04 莉諾兒現行角色 Bible 已將初遇年齡統一為九歲；09-P05 已改為「找到九歲的莉諾兒」，並移除「精確年齡仍不在本章鎖死」。

## CHG-2026-08-30-007

## DATE：2026-08-30 19:20 +08:00

## TYPE：CORRECTION / FIX / FORMAT

## SCOPE：01–08 設定總表｜01 亞德里安、04 莉諾兒；09_序章～第一篇章節大綱｜第二版 P05～P08 與「下一步」；小說正文第三版第一～第七章規則複檢

## BEFORE：CHG-2026-08-30-004 已將一般診療聖職者鎖為「牧師」，CHG-2026-08-30-006 已將幼年莉諾兒初遇改為無武器，但全量規則複檢仍發現設定總表殘留「P-05 隨行神官為貝倫」與「短刃在安全後被歸還」兩個舊字串。現行 09 的 P05～P08 內容段落亦誤套 Heading 2，且「下一步」仍停在已完成的 P01～P03 試寫工作。

## AFTER：亞德里安設定中的貝倫已統一為隨行牧師；莉諾兒心防節奏移除幼年短刃歸還，改以吊墜未被奪、限制逐步解除、村民／遺物紀錄、持續尋找倖存者與實際離開選項成立。09-P05～P08 僅章名保留 Heading 2，章內施工文字恢復 Normal text；「下一步」更新為施工 P08，並重申工作／近侍身分、耳尾信任與數年共同生活的先後限制。正文第一～第七章另依 00 完成雙輪冷讀與文風修正；純文風改寫不逐句建立 Canon 紀錄。

## REASON：作者要求全部再依現行規則檢查；本輪發現的是既有 Canon 已更新、但文件同步與格式未完全收乾淨的殘留，若不修正會使後續 Agent 讀到互相衝突的指示。

## AUTHORITY：作者 2026-08-30 最新明確指示＋00 根規則＋CHG-2026-08-30-004／006 的既有 Canon。

## COMPATIBILITY：NON-BREAKING / CORRECTION / DOCUMENT-ONLY

## VALIDATION：正文七個 Google Docs 原生 Tabs 保持第一章至第七章；正文搜尋「神官」「短刃」「不是因為」「這意味著」「唇角」「瞳孔」「胸口像」「空氣像」「一片空」均無命中。設定總表已無「P-05 隨行神官為貝倫」與「短刃在安全後被歸還」；09 已無幼年短刃，P05～P08 章內文字樣式與下一步均已重新對齊。

## CHG-2026-08-30-006

## DATE：2026-08-30 19:20 +08:00

## TYPE：CANON / FIX

## SCOPE：小說正文第三版第五～第七章、09_序章～第一篇章節大綱｜第二版 P05～P07、01–08 設定總表｜04 莉諾兒

## BEFORE：莉諾兒約九至十歲、重傷守在家人遺體旁時仍持有缺角短刃；第五章讓她以短刃反擊伊妲，第六章再以「歸還父親短刃」作為第一個信任裂口，第七章也把短刃當成她持續確認的安全物。這使幼年莉諾兒過早帶出受過戰鬥訓練／幼年刺客感。

## AFTER：初遇時莉諾兒明確沒有武器，只護著家人吊墜，靠縮身、推人、踢蹬與抓扯等孩童本能反抗陌生人接近；不得寫成受過訓練的攻防。伊妲在強制撤離時控制她的雙手，改以寬布帶束在身前後抱上車。第六章移除短刃保管／歸還事件，第一個可驗證的鬆動改成約第十天開始能在同一層走動、守衛不再堵死門口；第七章移除所有以刀作為安全物或信任證據的描寫。莉諾兒後期接受專業潛行／暗殺訓練與成年武器定位不受此修改影響。

## REASON：作者最新明確指示「小女孩還是別拿刀了吧」；讓九至十歲、重傷且剛經歷屠村的莉諾兒更像真實受創孩童，避免在初遇階段過早戰鬥角色化。

## AUTHORITY：作者 2026-08-30 最新明確指示。

## COMPATIBILITY：BREAKING / CANON / PROSE

## VALIDATION：正文第五～第七章已移除「短刃」與幼年持刀事件；09-P05～P07 已同步為無武器、本能反抗與走廊限制逐步鬆動；04 莉諾兒初遇 Canon 已明定「當時沒有武器」與「不得寫出幼年刺客感」。

## CHG-2026-08-30-005

## DATE：2026-08-30 11:38 +08:00

## TYPE：CANON / GOVERNANCE / FORMAT / FIX

## SCOPE：小說正文第三版第五～第七章、09_序章～第一篇章節大綱｜第二版 P05～P08、01–08 設定總表｜04 莉諾兒

## BEFORE：第四章以七歲亞德里安的精神系魔法失控與器具上鎖收尾，第五章卻直接切到莉諾兒第一人稱的屠村翌日，缺少三年時間跳躍與 POV 交接；同一章又壓入強制撤離、路上交談與報名、梵恩家療傷、數週／數月心防鬆動、自行留下、工作／報恩與耳尾事件，導致因果與關係進展過快。莉諾兒被帶走的過程亦未在現行 Canon 中明確鎖定「雙手被束後強制上車」與「路上幾乎不說話」。

## AFTER：原第五章拆為三章。第五章《不能把她留在這裡》明確以「三年後，亞德里安十歲」承接第四章，採亞德里安貼身第三人稱，只寫屠村後發現莉諾兒、她的極短拒絕與反抗、伊妲收刀、雙手束在身前後強制帶上車；吊墜始終留在她身上，路上不報姓名，亞德里安章末仍不知道她叫什麼。第六章《門外一直有人》改由莉諾兒第一人稱，寫抵達梵恩家後約十天的治療與高度警戒：前兩天近乎不說話、約第四天才報名、仍因傷勢與守衛無法離開、約第十天短刃歸還；信任只出現第一個裂口。第七章《門一直開著》把時間拉到數週至數月，透過守衛撤除、村民與遺物紀錄、持續尋找倖存者、正門可自由跨出與實際可行的其他去處，最後才讓莉諾兒自行選擇「先留」。工作、報恩、耳尾文化誤會與更深家人依附後移到 P08 或更後。09 已升為 v2.1 並同步 P05～P08；04 莉諾兒 Canon 已補強綁縛、低台詞量與數日／數月心防節奏。

## REASON：作者指出第四、第五章銜接「莫名其妙會看不懂」，並明確允許第五章拆成二至三章；同時再次確認莉諾兒是被強行綁上車、幾乎沒有說話，抵達梵恩家治傷後才以數日到數月慢慢鬆動心防。

## AUTHORITY：作者 2026-08-30 最新明確指示。

## COMPATIBILITY：BREAKING / CANON / STRUCTURE

## VALIDATION：正文目前共七個 Google Docs 原生分頁，依序為第一章至第七章；第五～第七章分頁名稱與 Heading 2 章名一致。第五章為亞德里安第三人稱限知，無莉諾兒姓名與完整交涉；第六章才首次由她說出「莉諾兒」；第七章直到確有其他去處後才自行選擇暫留。09 已不存在舊「09-P06｜一起去」章號，並改用現行第三人稱限知為主／第一人稱為輔的 POV 治理。

## CHG-2026-08-30-004

## DATE：2026-08-30 03:10 +08

## TYPE：CANON / GOVERNANCE / CLARIFICATION

## SCOPE：00、09-P02、小說正文第三版第二～第四章

## BEFORE：異世界一般診療者被統一稱為「神官」；00 仍殘留全書每章 2,000～3,000 字的舊通用限制，與作者後續指定的章別篇幅衝突。

## AFTER：一般診療與治療聖職者統一使用「牧師」；「神官」保留給較高階聖職者、神殿職位或確實具有該階級的角色；異世界診療者仍不得稱為「醫師」。章長改為服從作者最新章別目標，不再以舊 2,000～3,000 字通用值硬砍完整場景。第二、三章維持約 2,800～3,800 字，第四章維持約 3,000～4,200 字。

## REASON：作者最新明確修正「應該叫牧師吧，神官更高級」，並重申第二～第四章篇幅依原 09 章別目標。

## AUTHORITY：作者最新明確指示。

## COMPATIBILITY：BREAKING / TERMINOLOGY / GOVERNANCE

## VALIDATION：00 的術語、TERM-01、TERMS QA 與 LENGTH 規則已更新；09-P02 的一般診療稱謂已改為「牧師」；正文第二～第四章重新精修並冷讀，三章均無「神官」或異世界「醫師」殘留，章別篇幅與 Google Docs 文件分頁格式均維持現行要求。

## CHG-2026-08-30-003

DATE：2026-08-30 02:39 +08:00

TYPE：GOVERNANCE / FORMAT / DEPRECATION

SCOPE：專案 Google Drive 結構、00、00A、現行正文／設定／章綱、99_備份

BEFORE：現行正文、設定總表、章綱與低權威人格原型散放在專案根目錄；99_備份雖已建立，但正文仍保留多個只差一次局部微調、已被更新完整快照取代的版本，設定備份也保留較舊重複 00 快照。

AFTER：專案根目錄只保留 00、00A、10_現行創作資料、90_參考資料、99_備份。10_現行創作資料集中《小說正文第三版》、《01-08_小說設定總表｜角色・關係・劇情資料》、《09_序章～第一篇章節大綱｜第二版》；90_參考資料收納並重新命名「亞德里安原型參考｜綜合人格特質整合報告｜2026-08-19」。99_備份新增 03_治理紀錄備份，保留本次整理前的 00 與 00A 快照。正文備份改採里程碑保留制，只保留「P01-P04整體修正前」「P05全面重寫前」「章節命名與分頁重排前」三個主要節點；永久刪除五個已被後續快照取代的正文微調備份：P01規則校正前、P05情緒重寫前、文件分頁重整前、P05精修前、P05第一人稱重寫前；另刪除一份較舊且已被後續 00 快照與 Changelog 取代的「00_創作規則｜作者決策同步前備份｜2026-08-27」。現行文件 ID 均未改變。

REASON：降低根目錄與備份區的文件噪音，讓人工與 AI 能快速辨識現行施工來源、低權威參考與歷史快照，並避免模型誤讀舊備份。

AUTHORITY：作者 2026-08-30 明確要求「文件太多太雜要整理，沒用的刪了並記錄進修改歷史」。

COMPATIBILITY：DOCUMENT-ONLY / GOVERNANCE

VALIDATION：重新列出專案根目錄、10_現行創作資料、90_參考資料與 99_備份各子資料夾；確認現行文件仍存在且 Drive ID 不變，刪除項目不再出現在備份資料夾。

## CHG-2026-08-30-002

## DATE：2026-08-30 02:30 +08:00

## TYPE：GOVERNANCE / FORMAT

## SCOPE：專案根目錄、99_備份、00 根規則、00A Changelog

## BEFORE：重大修改前建立的正文、設定與規則備份散落在專案根目錄；備份位置主要依賴當次對話記憶，其他 Agent 無法只靠專案文件穩定找到。

## AFTER：於專案根目錄建立「99_備份」（ID：1SxtaRF6rgmiI7Sg2VKPjftl9jm-p0ugn），下設「01_正文備份」（ID：1QiYgr-QMHpT2V9UzNcEuEVt_Z6VgjmmD）與「02_設定與規則備份」（ID：1geWgGidi3IEwqdpegn-VgLJsSHE1XQMc）；將根目錄現有明確標示為備份的文件移入對應子資料夾。00 的現行文件導航與 VERSION GOVERNANCE 已記錄完整位置、用途與讀取限制；備份不具現行 Canon／治理權威。

## REASON：保持專案根目錄乾淨，並確保任何後續 Agent 不依賴聊天記憶也能定位備份、區分現行檔與歷史快照。

## AUTHORITY：作者 2026-08-30 最新明確指示。

## COMPATIBILITY：DOCUMENT-ONLY

## VALIDATION：根目錄保留現行正式文件與 99_備份入口；正文備份與設定／規則備份分流存放；00 可直接查到三個資料夾的位置與不得從備份施工的規則。

## CHG-2026-08-26-002

DATE：2026-08-26 19:14 +08:00

TYPE：CANON / FIX

SCOPE：00 根規則、01–08 設定總表、小說正文第三版 P-05、P-04～P-05 工作底稿

BEFORE：P-05 在進城前路旁發現莉諾兒；她仍能進行完整交涉、提出以工作交換救治、明說對貴族的不滿並在路上報姓名；伊妲收走短刃後抬人上車，村莊、家人遺體與吊墜未進入現場。

AFTER：梵恩車隊沿唯一道路穿過遭屠村莊，找到約九至十歲、重傷並守著家人與吊墜的莉諾兒；她以恐懼、一次短暫恐慌反抗及隨後的放棄掙扎為主，不進行完整交涉也不報姓名。女騎士伊妲控制短刃後，未取下吊墜，直接強制連人帶吊墜撤離；姓名延至 P-06。

REASON：使地理、傷勢、幼年狀態與莉諾兒人設一致，並以可見動作取代不合理台詞與旁白代述。

AUTHORITY：作者 2026-08-26 最新明確指示。

COMPATIBILITY：BREAKING / CANON / PROSE

VALIDATION：P-05 維持亞德里安第三人稱限知與約 2,000～3,000 個中文字；商旅只可能誤傳強行帶走倖存者，不牽涉屠村責任；P-01～P-04 無相關舊事實，故不改正文。

## CHG-2026-08-26-001

## DATE：2026-08-26 15:04 +08:00

## TYPE：CANON / GOVERNANCE / FIX

## SCOPE：00 根規則、01–08 設定總表、小說正文第三版 P-02～P-05、P-04～P-05 工作底稿

## BEFORE：根規則將全書鎖成第一人稱多 POV；P-05 讓莉諾兒自行放刀並同意上車，無法支撐她初期把亞德里安視為能決定亞人命運的貴族，也缺少日後「強行綁走莉諾兒」傳聞的可見來源；管家與家庭教師長期只有職稱。

## AFTER：全書改為第三人稱限知為主、第一人稱為輔，目標約 6：4並按章節／場景分配；P-05 改用亞德里安貼身第三人稱，寫成他在莉諾兒明確拒絕後下令收刀、強制撤離，道路商旅只看見反抗與帶走過程；補入亞德里安的宅男反應、難堪、猶豫與事後受影響；管家定名查爾曼，家庭教師定名羅德里克。

## REASON：落實作者對敘事人稱、人物情緒、初遇誤會與配角辨識度的最新要求，並讓後續傳聞與關係修復具有正文因果。

## AUTHORITY：作者 2026-08-26 最新明確指示。

## COMPATIBILITY：BREAKING / STYLE / CANON

## VALIDATION：00 的 POV 導航、施工規則、Hard Fail 與 QA 已改；01／04／06／新版事件層已補強制撤離與傳聞伏筆；P-05 為單一第三人稱限知場景，莉諾兒明確拒絕、反抗並說出「你們貴族都一樣」，兩名商旅目擊片面過程；配角姓名已在正文與設定中一致。

## CHG-2026-08-17-005

DATE：2026-08-17 13:45 +08:00

TYPE：GOVERNANCE / FORMAT / FIX

SCOPE：00、01–08 設定總表、00A

BEFORE：01–08 已合併，但 00 導航仍保留部分舊獨立文件入口；總表已有 AI 索引但尚未完成最終治理與歷史紀錄制度。

AFTER：以 01–08 設定總表作為角色／關係唯一現行入口；建立 00A 歷史修改紀錄；統一 Canon、TBD、EXAMPLE、DEPRECATED 的 AI 讀取規則與專業 Heading 結構。

REASON：避免 AI 從已刪除或舊版來源補回過時設定，並建立後續可追溯的版本治理。

AUTHORITY：作者 2026-08-17 最新指示＋00 VERSION GOVERNANCE。

COMPATIBILITY：NON-BREAKING / DOCUMENT-ONLY

VALIDATION：逐分頁核對內容、狀態標記、Heading、00 導航與 Changelog 互相引用。

## CHG-2026-08-17-004

DATE：2026-08-17

TYPE：GOVERNANCE

SCOPE：01–08 設定總表｜00 AI 讀取索引

BEFORE：各人物、關係與舊劇情資料雖已整合，但缺少單一 AI 權威順序與狀態圖例。

AFTER：建立 AI 讀取索引，明定作者最新指示 > 00 > 01–06 > 世界設定／新版大綱 > 歷史來源 > 07–08；缺資料標 TBD，不自行補成 Canon。

REASON：降低多來源衝突與模型自行補完造成的設定漂移。

AUTHORITY：00 根規則＋作者指示。

COMPATIBILITY：NON-BREAKING

VALIDATION：索引分頁存在且狀態順序可直接讀取。

## CHG-2026-08-17-003

DATE：2026-08-17

TYPE：DEPRECATION / CANON

SCOPE：全書舊劇情、07、08、09、舊正文事件鏈

BEFORE：舊毒殺線、八篇主線、事件 ID、伏筆鏈與終局方案仍可能被模型視為可延續劇情。

AFTER：PLOT RESET。舊小說劇情全部作廢；舊事件不得自動沿用。人物核心、關係硬邊界與世界底層設定仍有效。

REASON：作者決定全面重建故事主線。

AUTHORITY：作者 2026-08-17 明確指示。

COMPATIBILITY：BREAKING

VALIDATION：00、01、07、08 均具有作廢／DEPRECATED 標記。

## CHG-2026-08-17-002

DATE：2026-08-17

TYPE：DEPRECATION

SCOPE：07 舊主線、08 舊事件與伏筆

BEFORE：07／08 為後續章節與正文施工的劇情依據。

AFTER：07／08 僅保留歷史參考，AI AUTHORITY：NONE；除非作者明確要求回顧、比較或復用，不得作為現行劇情來源。

REASON：配合 PLOT RESET，防止歷史事件污染新版主線。

AUTHORITY：作者指示＋00。

COMPATIBILITY：BREAKING

VALIDATION：兩分頁頂部皆有 DEPRECATED／舊劇情封存標記。

## CHG-2026-08-17-001

DATE：2026-08-17

TYPE：GOVERNANCE / FORMAT

SCOPE：原 01–08 獨立人物／關係／劇情文件

BEFORE：01–08 分散於多份 Google Docs，AI 需跨文件尋找設定，容易拿錯版本。

AFTER：整合為單一原生多分頁 Google Doc「01-08_小說設定總表｜角色・關係・劇情資料」，並建立完整備份。

REASON：降低版本分裂、提升人工與 AI 導航效率。

AUTHORITY：作者指示。

COMPATIBILITY：DOCUMENT-ONLY

VALIDATION：逐分頁比對來源內容；主檔與備份均已驗證。

## CHG-2026-08-16-001

DATE：2026-08-16

TYPE：GOVERNANCE / FORMAT

SCOPE：00_創作規則

BEFORE：創作規則偏反 AI 檢查清單，部分條文過度鼓勵短句與碎句。

AFTER：重構為 PROJECT WRITING GUIDE；確立繁體中文白話文、第一人稱多 POV、中文完整句、場景密度、西幻時代語體、AI 分階段施工與 Hard Fail QA。

REASON：讓規則同時能約束中文行文、角色聲音、場景施工與 AI 自檢。

AUTHORITY：作者回饋＋中文寫作規則整備。

COMPATIBILITY：BREAKING / STYLE

VALIDATION：00 現行規則已包含 QUICK START、POV、WHITE PROSE、DIALOGUE、ERA、CHARACTER GUARDS、AI WORKFLOW、FINAL QA、VERSION GOVERNANCE。

## CHG-2026-08-30-001

# DATE：2026-08-30 02:30 +08:00

# TYPE：GOVERNANCE / FORMAT

# SCOPE：00 根規則、小說正文第三版文件分頁與讀者可見章名

# BEFORE：正文以 P-01／P-02 等作為讀者可見章名，文件另有只有章名的空白序章分頁；00 仍要求以原生換頁符號切章。

# AFTER：正文讀者可見章名統一改為「第一章｜章名、第二章｜章名……」；P01／P02 等僅保留作大綱與施工索引。正文每章使用 Google 文件原生文件分頁（Tabs），無實際序章正文時不建立空白序章分頁，亦不再用換頁符號模擬章節。

# REASON：改善手機開啟時的閱讀入口與章節辨識度，並讓正文格式與作者指定的文件分頁工作方式一致。

# AUTHORITY：作者 2026-08-30 最新明確指示。

# COMPATIBILITY：BREAKING / DOCUMENT-ONLY

# VALIDATION：小說正文第三版目前共五個文件分頁，依序為第一章至第五章；分頁名稱與各章 Heading 2 標題一致；00 FORMAT 規則已同步更新。

# 4｜後續新增模板

複製以下區塊新增，不要覆寫舊條目：

## CHG-YYYY-MM-DD-###

DATE：

TYPE：

SCOPE：

BEFORE：

AFTER：

REASON：

AUTHORITY：

COMPATIBILITY：

VALIDATION：
