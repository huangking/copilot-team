---
description: 启动一个功能：澄清 → 规格 → 拆任务 → 交给 Dev
agent: PM
argument-hint: 一句话描述需求，例如 "为订单页加导出 CSV"
---

以 PM 角色处理这个需求：

${input:feature}

要求：

1. 先读 `AGENTS.md`、相关代码与已有 `docs/specs/`，再提问；最多 3 个问题。
2. 写 `docs/specs/<id>.md`（用 `.agents/skills/pm-spec` 的模板），验收标准编号且可测。
3. 给出任务拆分与建议的 Dev 起点。
4. 最后用 handoff「开始实现」交给 Dev；不要把实现细节写进规格。
