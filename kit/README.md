# Copilot 并行 Agent 套件（可移植）

把 `/data/project/copilot-team` 里的四角色 + 并行任务能力，装进任意一个已有的 Git 仓库。
默认**不覆盖**任何已有文件。

## 一条命令

```bash
./kit/install.sh /path/to/your-repo
```

先看会做什么：

```bash
./kit/install.sh /path/to/your-repo --dry-run
```

覆盖已安装的 agent/skill（不会覆盖 `AGENTS.md` 和任务清单）：

```bash
./kit/install.sh /path/to/your-repo --force
```

## 装了什么

| 目标路径 | 内容 |
|---|---|
| `.github/agents/*.agent.md` | PM / Dev / Test / DevOps / Review Lead / Reviewer |
| `.agents/skills/*` | 4 个角色 playbook（CLI 和 VS Code 共用） |
| `scripts/parallel-worktrees.sh` | 手动建 worktree 的小工具 |
| `docs/parallel-tasks.md` | 并行任务清单（已存在则跳过） |
| `AGENTS.md` / `AGENTS.copilot.md` | 协作契约；已有 `AGENTS.md` 时写 `AGENTS.copilot.md` 供合并 |
| `.vscode/settings.json` | 合并缺失的 Copilot chat 设置，保留原有键 |

Agent 文件已经做了两处 CLI 适配：

- `tools` 里同时有 VS Code 名（`editFiles`）和 CLI 别名（`edit`），两边都能用；
- 加了 `include-custom-instructions: true` 和 `strict-tools-list: true`，子代理会读 `AGENTS.md`，且不会自动获得额外工具。

PM 的 `tools` 里**没有** `execute`，所以在 CLI 里也没有 shell。

## 装完必须做的三件事

1. **合并契约**：把 `AGENTS.copilot.md` 里的角色表、写作用域、命令表并进 `AGENTS.md`；
   命令必须换成新仓库真实命令（`make test`、`pnpm test` 等）。
2. **改角色细节**：agent 的 persona 是通用的；按新项目补“入口在哪、测试怎么跑、禁止动哪些目录”。
3. **填任务清单**：`docs/parallel-tasks.md` 里的行是示例，替换成真实任务；
   每行的写作用域必须落到具体路径，且互不相交。

## 任务清单怎么用

`docs/parallel-tasks.md` 是唯一任务源：

```text
| ID | 任务 | 写作用域 | 依赖 | Agent | 状态 | 分支 |
| T1 | 补安装文档 | README.md, docs/setup.md | - | dev | todo | parallel/t1 |
| T2 | utils 单测 | tests/utils/** | - | test | todo | parallel/t2 |
| T3 | CI 缓存 | .github/workflows/ci.yml | - | devops | todo | parallel/t3 |
```

- 只有编排者改状态；worker 只读。
- `依赖` 为 `-` 且状态 `todo` 的任务才可以同时跑。
- 每个任务一个 worktree / 分支。

交互式：

```text
/fleet 读取 docs/parallel-tasks.md，只执行 todo 且依赖已完成的任务。
按写作用域隔离，完成后更新状态并给出验证命令与输出。
```

无头：

```bash
copilot --fleet -p "读取 docs/parallel-tasks.md，执行所有可并行的 todo 任务" \
  --allow-tool write --allow-tool 'shell(git:*)' --allow-tool 'shell(make:*)'
```

写冲突风险高时，一任务一个 worktree：

```bash
copilot -w T1 -p "只做 docs/parallel-tasks.md 的 T1，遵守写作用域"
copilot -w T2 -p "只做 docs/parallel-tasks.md 的 T2，遵守写作用域"
```

## 手动安装（不想跑脚本）

```bash
cp -R kit/agents/.            /path/to/repo/.github/agents/
cp -R kit/skills/.            /path/to/repo/.agents/skills/
cp    kit/scripts/parallel-worktrees.sh /path/to/repo/scripts/
cp    kit/templates/parallel-tasks.template.md /path/to/repo/docs/parallel-tasks.md
# AGENTS.md 按 templates/AGENTS.template.md 手工合并
```

## 验证

```bash
# CLI：agent 能被列出
copilot --agent dev -p "只输出你的角色和可写路径"

# VS Code：Chat: Diagnostics 里确认 agents / instructions / skills 都加载了
# CLI 交互：/agent 列表里能看到 PM、Dev、Test、DevOps

# 任务清单可被读取
/fleet 读取 docs/parallel-tasks.md，列出当前可执行的任务，不要开始执行
```

## 注意

- 这是一份快照；源仓库的 agent 更新后，用 `--force` 重新安装，或手工同步。
- 安装器只在 Git 仓库里工作（worktree 需要）。
- 不会替你改 `AGENTS.md`、不会覆盖任务清单、不会动 `.vscode/settings.json` 里已有的键。
- `strict-tools-list` 让 CLI 严格按列表给工具；如果某个角色在 CLI 里缺工具，先检查 `tools` 里是否同时有 VS Code 名和 CLI 别名。
