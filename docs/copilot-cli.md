# 用 Copilot CLI 跑并行

CLI 原生就有两种并行，而且比 VS Code 里的 handoff 更接近"真并行"：

| 机制 | 并行单位 | 隔离 | 适合 |
|---|---|---|---|
| **`/fleet`**（或 `--fleet`） | 一次会话内的多个 subagent | 共享文件系统，不隔离 | 拆得开的实现/测试/文档；一次派多路 |
| **多会话 + `--worktree`** | 多个独立 session / 进程 | `-w` 自动建 worktree | 多个 feature 同时写，互不干扰 |

`/fleet` 是"一个 PM 带多个 worker"；`-w` 是"多个互不干扰的工作台"。两个可以叠加：每个 worktree 里各开一个 fleet 会话。

## 1. 交互式：/plan → /fleet

```bash
cd /data/project/copilot-team
copilot
```

会话里：

```text
/plan 按 docs/specs/0001-export-csv.md 实现 CSV 导出
```

规划完成后选 **Accept plan and continue in Autopilot execution mode + /fleet**；
或者退出 plan mode 自己发：

```text
/fleet 按 docs/specs/0001-export-csv.md 实现。用 @dev 写代码，
用 @test 补测试，用 @devops 更新发布记录。写作用域互不重叠。
```

运行中用 `/tasks` 看子代理：

- `↑` / `↓` 选择，`Enter` 看详情（完成后有 summary）
- `x` kill，`r` 移除已完成项，`Esc` 退出任务列表

## 2. 无头：--fleet -p

适合脚本/CI/批处理：

```bash
copilot --fleet -p "按 docs/specs/0001-export-csv.md 实现 CSV 导出，写完跑 make test" \
  --allow-tool write \
  --allow-tool 'shell(make:*)' \
  --deny-tool 'shell(git push)'
```

要点：

- `--fleet` 必须配 `-i`、`-p` 或 stdin 之一，单独用没有效果。
- `-p` 非交互，权限要么用 `--allow-tool` 精确放行，要么用 `--yolo`（不推荐）。
- 输出用 `--output-format=json`（JSONL）方便程序消费；`-s` 只看最终答复。
- `--fleet` 不能和 `--acp` 一起用；`copilot workflow run` 也不能和 `--fleet` 组合。

## 3. 多 worktree：-w

每个 feature 一个独立工作区，互不覆盖：

```bash
# 终端 1
copilot -w csv-export

# 终端 2
copilot -w due-date
```

`-w` 会在 `<repo>.worktrees/<name>` 建 worktree 并切到新分支，会话直接在里面工作。
也可以叠加 fleet：

```bash
copilot -w csv-export --fleet -p "实现 CSV 导出，测试全绿后提交"
```

注意：`-w` 与 `--resume` / `--continue` / `--connect` 冲突；worktree 从当前 `HEAD` 建，未提交改动不会带过去。

一个进程里也可以开多个 session（`n` 新建，`←` 打开 sidebar，`↑/↓` 切换），切走的 session 会继续跑。

## 4. 四个角色怎么映射

| 角色 | 在 CLI 里 |
|---|---|
| PM | 主会话（orchestrator）；`/plan` 出计划，`/fleet` 派活 |
| Dev | custom agent `dev`，fleet 里用 `@dev` 指定 |
| Test | custom agent `test`，`@test` |
| DevOps | custom agent `devops`，`@devops` |
| 评审 | `review-lead` / `reviewer`（并行只读评审） |

CLI 会自动加载 `.github/agents/`（项目级）和 `~/.copilot/agents/`（用户级）：

```bash
copilot --agent dev -p "实现 docs/specs/0001-export-csv.md 的 AC-1~AC-4"
```

`--agent` 接受文件 ID（`dev`）或 `name`（`"Dev"`，加引号）。fleet 里用 `@dev` 这种 ID 最稳。

### 工具名要换成 CLI 的别名

VS Code agent 文件里的 `readFile` / `editFiles` / `runInTerminal` 在 CLI 里是**未识别工具名**（会被忽略）。CLI 认这些别名：

| 能力 | CLI 别名 |
|---|---|
| 读文件 | `read` |
| 改文件 | `edit` |
| 搜索 | `search` |
| 执行命令 | `execute` |
| 调子代理 | `agent` |
| 网页 | `web` |
| 待办 | `todo` |

所以让同一批 agent 在 CLI 里可用，需要把别名加进 `tools`，例如 Dev：

```yaml
tools: ['search', 'readFile', 'read', 'editFiles', 'edit', 'runInTerminal', 'execute', 'runTests', 'problems', 'changes', 'todos', 'todo']
```

PM 只加 `read` / `edit` / `web` / `todo`，**不要加 `execute`**，否则 PM 在 CLI 里就有了 shell。

另外：custom agent 作为 subagent 运行时，默认**不加载仓库自定义指令**（`AGENTS.md`）。需要它遵守仓库约定，就在 frontmatter 加：

```yaml
include-custom-instructions: true
```

## 5. 权限与成本

- `/fleet` 的每个子代理都是独立模型调用，会成倍消耗 AI credits；用 `--max-ai-credits` 设上限。
- 子代理共享文件系统：`/fleet` 不做 worktree 隔离，写同一文件仍会冲突。要隔离就 `-w`。
- 默认会询问权限；无人值守时用最小授权的 `--allow-tool`，别直接 `--yolo`。
- `--sandbox` 可给 shell 加 OS 级沙箱（Linux/macOS），`-p` 场景尤其值得开。

## 6. 三种并行怎么选

| 场景 | 选择 |
|---|---|
| 一次任务能拆成 3~4 个独立子任务 | `/fleet` 或 `--fleet -p` |
| 多个 feature 要同时改同一仓库 | 多个 `copilot -w <name>` 进程 |
| 既要隔离又要内部并行 | `copilot -w <name> --fleet` |
| 想要人审每一步 | VS Code 的 handoff（串行） |
| 要 PR 协作 | 云端 coding agent（issue → PR） |

## 7. 常见问题

**Q：`/fleet` 没并行？**
任务本身是串行的，或者 prompt 太模糊。给明确的文件/目标，例如"`.md` 文档三份分别写""auth 模块重构 + 测试 + 文档"。

**Q：子代理没有按仓库规范写？**
加 `include-custom-instructions: true`，或者在 fleet prompt 里明确"先读 AGENTS.md"。

**Q：CLI 里的 Dev 没有编辑工具？**
`tools` 里只有 `editFiles`，CLI 不认；加 `edit`（以及 `read`、`execute`）。

**Q：多个 worktree 会话互相影响吗？**
不会，各自独立分支/目录；但共享 `.git`，不要在同一 worktree 里同时跑两个会话写同一文件。
