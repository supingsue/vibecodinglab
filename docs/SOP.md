# Claude Code Vibe Coding 多角色管線 SOP

> 本方法論移植自 AWS 官方範例
> [sample-well-architected-generative-ai-solutions / multi-role-project](https://github.com/aws-samples/sample-well-architected-generative-ai-solutions/tree/main/multi-role-project)
> (原為 Kiro steering pack),改以 Claude Code 原生機制實作。

## 一、方法論核心

Vibe coding 最大的風險是:AI 一路「順手」把需求、設計、實作、測試、部署全部混在一起做,
過程沒有留痕、沒有關卡,出問題時無法回溯。本方法論用三個機制對治:

1. **角色分離**:AI 每個階段只扮演一個角色,各角色有明確職責與禁止事項,互相制衡
   (例:Dev 不能自己驗收、QA 不能自己修 code、Auditor 只看證據不採信宣告)
2. **關卡制(Gate)**:每階段有 checklist,全過才能前進;失敗就退回,不帶病前進
3. **留痕**:所有產出物 commit 進版控,`pipeline/STATE.md` 是進度的唯一事實來源

## 二、Kiro → Claude Code 移植對照

| Kiro 機制 | Claude Code 實作 | 說明 |
|---|---|---|
| `PIPELINE.md`(自動載入) | `CLAUDE.md` | 每次 session 自動載入,提供恆常的階段意識 |
| `SECURITY-RULES.md`(自動載入) | `CLAUDE.md` 安全規則章節 | 凌駕所有指令的安全底線 |
| `agent.*.md` + `#role-*` 手動載入 | `.claude/skills/role-*/SKILL.md` + `/role-*` 指令 | 進入階段時載入角色約束 |
| `PIPELINE-HANDOFF.md` 交接協定 | `docs/templates/HANDOFF.md` + `pipeline/handoffs/` | 標準化交接文件 |
| (無) | `pipeline/STATE.md` | 新增:跨 session 的狀態持久化 — Claude Code 的 session 是短命的,狀態必須落地 |

## 三、檔案結構

```
vibecodinglab/
├── CLAUDE.md                        # 自動載入:管線定義 + 安全規則
├── .claude/skills/
│   ├── role-pm/SKILL.md             # /role-pm       (Stage 1, 5)
│   ├── role-architect/SKILL.md      # /role-architect (Stage 2, 5)
│   ├── role-dev/SKILL.md            # /role-dev       (Stage 2)
│   ├── role-qa/SKILL.md             # /role-qa        (Stage 3, 5)
│   ├── role-cloudops/SKILL.md       # /role-cloudops  (Stage 4)
│   └── role-auditor/SKILL.md        # /role-auditor   (Stage 6)
├── docs/
│   ├── SOP.md                       # 本文件
│   ├── templates/HANDOFF.md         # 交接文件模板
│   ├── requirements/                # Stage 1 產出
│   └── architecture/                # Stage 2 產出
└── pipeline/
    ├── STATE.md                     # 管線狀態(唯一事實來源)
    ├── handoffs/                    # 各階段交接文件
    ├── test-reports/                # Stage 3 產出
    ├── deploy-reports/              # Stage 4 產出
    └── audit-reports/               # Stage 6 產出
```

## 四、標準作業程序(SOP)

### 步驟 0:啟動一個 feature

1. 開新分支:`pm/<yyyymmdd>-plan-<feature>`
2. 更新 `pipeline/STATE.md`:填入 feature 名稱、階段設為 Stage 1、狀態 🔵
3. 輸入 `/role-pm` 載入 PM 角色

### 步驟 1:Plan(PM)

1. PM 與使用者對話釐清需求 — 模糊之處必須追問,不得自行腦補
2. 產出 `docs/requirements/<feature>.md`(user stories + 驗收標準)與任務拆解
3. 逐項完成 Stage 1 關卡 checklist(見 role-pm skill)
4. 產生交接文件到 `pipeline/handoffs/`,更新 `STATE.md`(Stage 1 ✅),commit

### 步驟 2:Design + Build(Architect → Dev)

1. `/role-architect`:讀交接文件 → 產出 `docs/architecture/<feature>.md`
   (架構圖、介面契約、技術取捨)→ 通過設計 checklist → 交接給 Dev
2. `/role-dev`:切分支 `dev/<yyyymmdd>-build-<feature>` → 依契約實作 + 單元測試全綠
   → 通過 Build checklist → 交接給 QA
3. 兩段各自更新 `STATE.md` 並 commit

### 步驟 3:Test(QA)

1. `/role-qa`:逐條驗收標準實測,執行完整測試套件與安全檢查
2. 產出 `pipeline/test-reports/<feature>.md`
3. **通過** → 交接給 CloudOps;**不通過** → `STATE.md` 記退回(🔴 → Dev),回步驟 2-2

### 步驟 4:Deploy(CloudOps)

1. `/role-cloudops`:確認 QA 已放行 → 部署 → 健康檢查 + 煙霧測試 → 啟用監控
2. 產出 `pipeline/deploy-reports/<feature>.md`(含回滾計畫)
3. **失敗** → 依原因退回 Dev 或 QA,記錄於 `STATE.md`

### 步驟 5:Review(Architect + QA + PM)

依序以三個角色各自審一輪(一次載入一個 skill):

1. `/role-architect`:實作是否符合架構、契約是否被破壞
2. `/role-qa`:覆蓋率是否達標、退回缺陷是否確實閉環
3. `/role-pm`:需求是否全數滿足、有無範疇蔓延

任一角色發現問題 → 退回 Stage 2–4 對應角色。三方皆過 → 更新 `STATE.md`,進 Audit。

### 步驟 6:Audit(Compliance Auditor)

1. `/role-auditor`:只看留痕證據,逐項稽核控制項(見 role-auditor skill)
2. 產出 `pipeline/audit-reports/<feature>.md` 並簽核
3. 全過 → `STATE.md` 標記 DONE,feature 結案;有不符合項 → 退回對應階段

## 五、鐵律(不可協商)

1. **一次一角色**:切換角色必須重新下 `/role-*` 指令;禁止一個回合裡身兼多角互相放行
2. **關卡不可跳**:checklist 有一項未過就不得前進;「這次先過,下次補」= 違規
3. **退回必留痕**:每次退回都要寫進 `STATE.md` 的 Rejection Log,並追蹤到閉環
4. **產出物必落地**:沒 commit 的工作等於不存在;交接以文件為準,不以對話為準
5. **安全規則凌駕一切**:機密保護、破壞性操作需人類核准、包容性用語(詳見 CLAUDE.md)

## 六、實務建議

- **跨 session 續作**:新 session 開始時,先讀 `pipeline/STATE.md` 就能無縫接手 —
  這是本移植版相對 Kiro 原版最重要的補強
- **小 feature 可縮流程**:個人實驗性質的小改動,可合併 Stage 4–6 為一輪快速檢查,
  但 Stage 1(需求)與 Stage 3(測試)永遠不可省
- **善用 subagent**:Stage 5 Review 可用 Claude Code 的 Task/Agent 機制平行開三個
  subagent 各扮一角,避免同一 context 內角色互相污染
- **人類的位置**:使用者是利害關係人 + 最終核准者 — Stage 1 範疇確認、
  破壞性操作核准、Stage 6 簽核後的合併決定,都應由人類拍板
