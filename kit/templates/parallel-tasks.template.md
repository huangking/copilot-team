# 并行任务清单

> 本文件是 `/fleet` 与 `copilot -w` 的**唯一任务源**。
> 只有编排者（PM / 主会话）更新状态；worker 只读。

## 规则

- 一行一个任务；ID 用 `T1`、`T2` 这种短编号。
- 写作用域必须是互斥的路径前缀；有交集的任务不能同时跑。
- `依赖` 为 `-` 才能立即开始；否则等依赖任务 `done`。
- 每个任务一个分支 `parallel/<id>`（或 `-w` 自动生成的 worktree）。
- 状态：`todo` / `doing` / `done` / `blocked`。
- 完成后由编排者更新状态，并把验证命令与实际输出写进对应产物。

## 任务

| ID | 任务 | 写作用域 | 依赖 | Agent | 状态 | 分支 |
|---|---|---|---|---|---|---|
| T1 | <!-- 例：补 README 的安装与运行章节 --> | `README.md`, `docs/setup.md` | - | dev | todo | `parallel/t1` |
| T2 | <!-- 例：为 utils 模块补单元测试 --> | `tests/utils/**` | - | test | todo | `parallel/t2` |
| T3 | <!-- 例：CI 增加依赖缓存 --> | `.github/workflows/ci.yml` | - | devops | todo | `parallel/t3` |
| T4 | <!-- 例：把 API 文档拆成三份 --> | `docs/api/**` | - | dev | todo | `parallel/t4` |

> 上面的行是示例，复制到新仓库后替换成真实任务；写作用域一定要落到具体路径。

## 怎么跑

**交互式（推荐先试）**

```text
/fleet 读取 docs/parallel-tasks.md，只执行状态为 todo 且依赖已完成的任务。
每个任务按写作用域隔离，完成后更新状态，并给出验证命令与输出。
```

**无头**

```bash
copilot --fleet -p "读取 docs/parallel-tasks.md，执行所有可并行的 todo 任务" \
  --allow-tool write --allow-tool 'shell(git:*)' --allow-tool 'shell(make:*)'
```

**一任务一个 worktree（写冲突风险高时）**

```bash
copilot -w T1 -p "只做 docs/parallel-tasks.md 的 T1，遵守写作用域"
copilot -w T2 -p "只做 docs/parallel-tasks.md 的 T2，遵守写作用域"
```

## 集成顺序

<!-- 合并 PR / 分支的顺序；冲突谁修。 -->

1. T1
2. T2
3. T3

## 完成记录

| 任务 | 结果 | 证据 / PR |
|---|---|---|
| T1 |  |  |
