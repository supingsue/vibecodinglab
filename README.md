# vibecodinglab

Claude Code vibe coding 實驗室 — 內建「多角色交付管線」方法論。

AI Agent 依六個階段切換專業角色(PM → Architect → Dev → QA → CloudOps → Auditor),
每階段有明確產出物與關卡(Gate),未通過即退回,全程留痕於版控。

## 快速開始

1. 在本 repo 開啟 Claude Code(`CLAUDE.md` 會自動載入管線規則與安全底線)
2. 輸入 `/role-pm` 開始 Stage 1,描述你要做的 feature
3. 依關卡逐階段推進;進度隨時看 `pipeline/STATE.md`

## 文件

- **完整 SOP**:[docs/SOP.md](docs/SOP.md)
- 管線規則與安全規則:[CLAUDE.md](CLAUDE.md)
- 角色定義:`.claude/skills/role-*/SKILL.md`
- 交接模板:[docs/templates/HANDOFF.md](docs/templates/HANDOFF.md)

## 方法論來源

移植自 AWS 官方範例 [sample-well-architected-generative-ai-solutions / multi-role-project](https://github.com/aws-samples/sample-well-architected-generative-ai-solutions/tree/main/multi-role-project)(Kiro steering pack),改以 Claude Code 原生機制(CLAUDE.md + Skills)實作。
