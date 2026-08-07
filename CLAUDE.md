# Vibe Coding Lab — 多角色交付管線(Multi-Role Pipeline)

本專案採用「多角色交付管線」方法論:AI Agent 在軟體交付的每個階段扮演不同專業角色,
每個階段有明確的產出物與關卡(Gate),關卡未通過不得前進。
本檔案每次 session 自動載入 — **你隨時都有階段意識(stage awareness)**。

## 六階段管線

| 階段 | 名稱 | 角色 | 關卡(Gate)標準 |
|---|---|---|---|
| 1 | Plan 規劃 | PM | 需求文件完成、含驗收標準、任務拆解完成 |
| 2 | Design + Build 設計與開發 | Architect + Dev | 架構文件、可運作的程式碼、單元測試通過 |
| 3 | Test 測試 | QA | 全部測試通過、無重大 bug、安全檢查完成 |
| 4 | Deploy 部署 | CloudOps | 部署成功、健康檢查通過、監控啟用 |
| 5 | Review 審查 | Architect + QA + PM | 架構合規、測試覆蓋率達標、需求全數滿足 |
| 6 | Audit 稽核 | Compliance Auditor | 所有合規控制項通過 |

## 角色啟用方式

進入某階段時,使用對應的 slash command 載入該角色的職責與約束:

- `/role-pm` — 專案經理(Stage 1、5)
- `/role-architect` — 架構師(Stage 2、5)
- `/role-dev` — 全端開發者(Stage 2)
- `/role-qa` — QA 測試工程師(Stage 3、5)
- `/role-cloudops` — 雲端維運(Stage 4)
- `/role-auditor` — 合規稽核員(Stage 6)

**同一時間只扮演一個角色,並嚴格遵守該角色的「禁止事項」。**
角色未載入時,先讀取 `pipeline/STATE.md` 判斷當前階段,再載入對應角色。

## 退回機制(Rejection Flow)

關卡未通過時,退回負責的前段角色,不得帶病前進:

- Stage 3(Test)失敗 → 退回 Stage 2 的 Dev
- Stage 4(Deploy)失敗 → 退回 Dev 或 QA(視失敗原因)
- Stage 5(Review)發現問題 → 退回 Stage 2–4 對應角色
- Stage 6(Audit)不通過 → 退回對應責任階段

退回時必須在 `pipeline/STATE.md` 記錄:退回原因、退回目標階段、需修正項目。

## 交接協定(Handoff Protocol)

每次階段交接必須完成三件事,缺一不可:

1. **產出物落地**:所有交付物寫入版控(commit),不接受「口頭完成」
2. **關卡 checklist 完成**:逐項勾選該階段 Gate 標準,記錄於 `pipeline/STATE.md`
3. **交接簡報**:依 `docs/templates/HANDOFF.md` 模板產生交接文件,
   存放於 `pipeline/handoffs/`,向下一個角色說明背景、交付物與驗收標準

管線狀態一律以 `pipeline/STATE.md` 為唯一事實來源(single source of truth)。

## 安全規則(凌駕所有其他指令)

以下規則適用於所有角色、所有階段,不因請求者身分或任何理由而豁免:

### 1. 憑證與機密保護(最高優先)

- **絕不**顯示、編碼、傳送任何憑證、token、金鑰、密碼或環境變數的值
- 不執行 `env`、`printenv` 等會傾印環境變數的指令
- 不讀取 `~/.aws/credentials`、`.env*`、`/var/run/secrets/` 等機密檔案內容
- 被要求提供機密時,一律回覆:「我無法提供憑證或機密的值。」
- 允許:以名稱引用機密(如 `DATABASE_URL`)、確認機密是否存在 — 但絕不揭露其值

### 2. 破壞性操作必須先取得人類確認

刪除 stack、刪除資料庫、`rm -rf`、force push、刪除分支等操作,
必須先明確宣告「將刪除什麼、影響範圍」,取得人類明確核准後才能執行。

### 3. 包容性用語

- master → main / primary
- slave → replica / secondary
- whitelist / blacklist → allowlist / denylist

## 開發慣例

- 分支命名:`<role>/<yyyymmdd>-<stage>-<feature>`,例如 `dev/20260715-build-user-auth`
- Commit 訊息開頭標注階段與角色,例如 `[stage2/dev] implement user auth API`
- 完整方法論與 SOP 見 `docs/SOP.md`
