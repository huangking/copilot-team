# taskboard · VS Code + GitHub Copilot 多 Agent 练习仓库

这是一个**故意保持很小**的 Python 项目，用来把 4 个角色（PM / Dev / Test / DevOps）真正跑起来：

- 领域逻辑：`src/taskboard/core.py`（纯函数，无 I/O）
- CLI：`src/taskboard/cli.py`（JSON 文件持久化）
- 测试：`tests/`（44 个用例，全部通过）
- 示例任务：`docs/specs/0001-export-csv.md`（已实现并通过验证，见 `docs/test-reports/`）

四个 Agent 的配置都在仓库里，换台机器 clone 下来就能用。

## 快速开始

```bash
python3 -m pip install pytest
make test          # 44 passed
make lint
PYTHONPATH=src python3 -m taskboard add "写规格"
PYTHONPATH=src python3 -m taskboard list
```

## 团队

| Agent | 文件 | 能做什么 | 不能做什么 |
|---|---|---|---|
| **PM** | `.github/agents/pm.agent.md` | 读代码、写规格/验收标准、派活 | 不写业务代码、不跑 shell |
| **Dev** | `.github/agents/dev.agent.md` | 改 `src/`、写测试、跑测试 | 不改验收标准、不发布 |
| **Test** | `.github/agents/test.agent.md` | 独立验证、写测试与报告 | 不修 `src/` |
| **DevOps** | `.github/agents/devops.agent.md` | 改 CI/镜像、写发布与回滚 | 不碰业务代码 |

约束写在 `AGENTS.md`；角色 playbook 在 `.agents/skills/`（Copilot 与 DSH 共用）。

## 跑一遍完整流程

1. 打开仓库，Chat 里把 agent 切到 **PM**。
2. 输入：`/feature-kickoff 实现 CSV 导出`，或直接说
   > 请按 docs/specs/0001-export-csv.md 推进：确认验收标准，拆任务，然后交给 Dev。
3. PM 会读 `AGENTS.md`、`docs/specs/`，产出/确认规格，然后出现 **开始实现** 按钮。
4. 点 **开始实现** → 切到 **Dev**：先写 `docs/plans/0001-export-csv.md`，再改代码，最后跑 `make test`。
5. 点 **验证实现** → 切到 **Test**：按 AC 建矩阵、跑测试、写 `docs/test-reports/0001-export-csv.md`。
6. 失败就点 **修复失败项** 回 Dev；通过就点 **准备发布** → **DevOps** 写 `docs/releases/` 并跑 `release` workflow（手动触发）。
7. 人审 PR；需要额外视角时用 Copilot code review。

> Handoff 是**人工门禁**：按钮出现后需要你点，prompt 才会发出去。这是刻意设计，不是缺陷。

## 校验配置是否生效

- `Chat: Diagnostics`（命令面板）：确认 4 个 agent、2 个 instructions、4 个 skills 已加载，且没有工具名告警。
- `/agents`：下拉框里应出现 PM / Dev / Test / DevOps。
- 发一句 "只输出你的角色和可写路径"：四个 agent 的回答应该不同。

## 目录

```
.
├── AGENTS.md                     # 全员契约（角色边界、产物、命令、DoD）
├── .github/
│   ├── agents/                   # 4 个 custom agent（frontmatter + prompt）
│   ├── instructions/             # tests/**、infra/** 的按路径规则
│   ├── prompts/feature-kickoff.prompt.md
│   └── workflows/{ci,release}.yml
├── .agents/skills/               # 4 个角色 playbook（Copilot + DSH 共用）
├── .vscode/                      # 推荐扩展与 chat 配置
├── docs/{specs,plans,test-reports,releases}/
├── src/taskboard/{core,cli,__main__}.py
├── tests/
├── Makefile
├── Dockerfile
└── pyproject.toml
```

## 并行模式

`PM → Dev → Test → DevOps` 的 handoff 链是串行的（同一会话、人工确认、下游依赖上游）。要并行有三种方式：

- **多会话 / worktree**：每个任务一个会话；后台 agent 自动 worktree，本地会话可用 `scripts/parallel-worktrees.sh` 建隔离目录。
- **Subagent fan-out**：选中 **Review Lead**，它并行跑多个只读 **Reviewer** 子代理（正确性/安全/性能/兼容），汇总后交回 Dev。
- **云端**：一个 issue 一个 Copilot coding agent，各自开 PR。

拆分规则、不能并行的场景、集成检查单见 [docs/parallel-playbook.md](docs/parallel-playbook.md)；
手把手的操作步骤见 [docs/parallel-runbook.md](docs/parallel-runbook.md)。
用 Copilot CLI 的话，`/fleet`（会话内并行子代理）和 `-w`（每个任务一个 worktree）是另一套入口，见 [docs/copilot-cli.md](docs/copilot-cli.md)。
把这套能力搬到别的仓库：`./kit/install.sh /path/to/repo`（默认不覆盖已有文件），见 [kit/README.md](kit/README.md)。

## 已知取舍

- `tools` 名称随 VS Code 版本变化；写错会被静默忽略，以 `Chat: Diagnostics` 为准。
- PM 的 `editFiles` 没有路径级限制，靠 `AGENTS.md` + review 兜底；要硬隔离需要换工具链。
- Handoff 不开新会话，长会话上下文会膨胀；每次 handoff prompt 只指向 spec 文件与 diff。
- 这个仓库的 `release.yml` 只构建镜像、不推送；真实发布需要加 registry 凭据与审批。

## 推到 GitHub

```bash
gh repo create taskboard-copilot --private --source . --push
```

然后在仓库 Settings → Actions 里确认 workflow 权限为 read-only。
