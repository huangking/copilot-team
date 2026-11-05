# 并行模式：Copilot 多 Agent 能不能同时跑

结论：**能并行，但要先分清"哪一层"在并行**。

- `PM → Dev → Test → DevOps` 的 **handoff 链本身是串行的**：它在同一个会话里交接，每一步要人点按钮，下游依赖上游产物。这条链不该并行。
- 可以并行的是**任务之间**（不同 feature / 不同评审角度 / 不同变体），以及**一个会话内部的只读 fan-out**（subagent）。

## 三种并行单位

| 模式 | 并行单位 | 隔离方式 | 适合 | 主要代价 |
|---|---|---|---|---|
| **A. 多会话** | 每个任务一个 agent session | 本地会话共享工作区；后台 agent 自动 worktree | 独立 feature、调研、文档 | 共享工作区会互相覆盖；需要人切换 |
| **B. Subagent fan-out** | 一次回复里的多个子代理 | 各自独立上下文；工具随子代理配置 | 只读评审、测试矩阵、方案对比 | 同步等待；子代理结果只回摘要 |
| **C. 云端任务** | 每个 issue 一个 coding agent | GitHub 远程环境 + 独立 PR | 可并行的 feature、批量修复 | 并发额度；PR 合并冲突；反馈慢 |

### A. 多会话并行（最常用）

VS Code 允许**同时存在多个 agent session**，新建会话时旧会话继续运行，在 Chat 的 sessions list 里切换。三种会话类型：

1. **Local**：共享当前工作区。适合互不写同一文件的活（调研、写不同文档、分别评审）。两个本地会话同时改 `src/` 会互相覆盖。
2. **Background**（Copilot CLI）：每个会话自动创建 **Git worktree**，改动隔离在独立目录，每轮结束提交；完成后在 sessions list 里查看 diff，再 apply 回主工作区。
3. **Cloud**（Copilot coding agent）：远程跑，产出 PR；适合"一个 issue 一个 PR"的并行交付。

后台/云端会话还能选 custom agent（后台选 custom agent 目前是实验特性，需要开启
`github.copilot.chat.cli.customAgents.enabled`，且只认工作区里的 agent 文件）。

### B. Subagent fan-out（一次回复内并行）

在**同一个 agent 的同一轮**里，可以派多个 subagent 并行跑，等全部返回后汇总。适合：

- 一个 PR 的多视角评审：正确性 / 安全 / 性能 / 兼容性
- 测试矩阵拆分：单元 / 端到端 / 兼容性 / 回归
- 方案对比：三个实现思路各写一份评估

限制：

- subagent 是**同步**的：主 agent 等所有子代理结束才继续。
- 默认继承主会话的模型与工具；要不同工具/模型，需要把 custom agent 作为 subagent（实验特性）。
- 子代理之间不共享上下文，prompt 必须自包含。
- **不要用 subagent 并行写同一片文件**；只读或写各自独立文件才安全。

本仓库提供了一个现成入口：选中 **Review Lead** agent，它会并行跑多个 **Reviewer** 子代理并汇总。Reviewer 是只读的（`search` / `readFile` / `usages`），不会碰代码。

### C. 云端并行

把规格拆成多个 issue，每个 issue 分配给 Copilot coding agent，各自开 PR。适合：

- 多个互不依赖的小 feature
- 同一 feature 的多个独立模块
- 批量修复（每个 issue 一个修复）

注意：并发数受套餐限制，超出会排队；PR 之间仍会有合并冲突，需要集成顺序。

## 什么不能并行

- **同一 feature 的角色链**：Dev 没产出，Test 无法验证；Test 没过，DevOps 不该发布。handoff 是人工审批门，故意串行。
- **同一文件的多个 writer**：包括 `cli.py`、`core.py` 这种共享入口。
- **有依赖的迁移/重构**：先后顺序本身就是正确性的一部分。
- **需要同一份编辑器上下文的活**：后台 agent 拿不到 VS Code 的失败测试、选中代码等运行时上下文。

## 拆分规则（决定能不能真并行）

1. **写作用域互斥**：每个任务声明自己会改的路径前缀，任意两个任务的交集必须为空。
2. **共享文件单一 owner**：`pyproject.toml`、`cli.py`、`AGENTS.md` 这类文件指定一个"集成者"，其他人只提需求。
3. **依赖显式化**：`A blocks B` 写进 spec 的并行批次表；被 block 的任务不要提前开跑。
4. **集成顺序固定**：先合谁、后合谁、冲突谁修，先写清楚。
5. **任务足够小**：一个任务一个 worktree/PR，半天内能 review 完。

## 在本仓库怎么用

本仓库的 `core.py` 与 `cli.py` 是共享入口，**CSV 导出这类 feature 不适合再拆成并行写**。可并行的切片：

| 切片 | 谁做 | 写哪里 | 依赖 |
|---|---|---|---|
| 多视角评审当前 diff | Review Lead（并行 subagent） | 只读 | 无 |
| 测试矩阵补充（边界/错误/兼容） | 多个 Test 会话或 subagent | `tests/**` 各自文件 | 实现已完成 |
| 文档/发布记录 | PM/DevOps 独立会话 | `docs/**` | 无 |
| 两个独立 feature（各自模块） | 两个后台会话 | 各自新文件 | 需要先把 CLI 拆成 `commands/` |

### 并行实现的操作步骤

```bash
# 1) 建两个隔离 worktree（分支 parallel/<name>）
scripts/parallel-worktrees.sh create export-csv due-date

# 2) 每个目录单独开一个 VS Code 窗口
code ../taskboard-copilot.worktrees/export-csv
code ../taskboard-copilot.worktrees/due-date

# 3) 每个窗口里开一个会话，选对应 agent，prompt 里带上任务边界
#    完成后各自提交、开 PR

# 4) 查看/清理
scripts/parallel-worktrees.sh list
scripts/parallel-worktrees.sh remove export-csv
```

每个任务的 prompt 模板：

```text
任务：<task-id>，只实现 docs/specs/<id>.md 中分配给本任务的条目。
写作用域：只允许改 <path-a>、<path-b>；其他文件一律不动。
依赖：<无 / 依赖 task-x 已合并>。
交付：代码 + 测试 + docs/plans/<id>.md，跑 make test 并贴输出。
```

### 集成检查单

- [ ] 每个 worktree/PR 的写作用域没有交集
- [ ] 每个 PR 单独跑过 `make lint && make test`
- [ ] 合并顺序与 spec 的批次表一致
- [ ] 合并后主干再跑一次全量测试
- [ ] 有冲突时由"集成者"统一解决，不让两个 agent 互相 rebase

## 成本与限额

- 并行会成倍消耗 premium requests / token；评审和测试 fan-out 尤其明显。
- 云端 coding agent 有并发额度，超出会排队。
- 真正稀缺的是**人的 review 带宽**：并行 5 个 PR，最后还是要你逐个看。

## 和 DSH 的对应关系

| 能力 | Copilot | DSH |
|---|---|---|
| 会话内并行 | subagent 并行（同步） | `workflow` 的 `parallel()`（同步）、多个 `subagent`（异步） |
| 工作区隔离 | 后台 agent 自动 worktree | 实验性 worktree 工具 + sandbox |
| 异步任务 | background / cloud agent | `subagent` 完成通知、`send_message` 续聊 |
| 任务板 | GitHub Issues/Projects | 实验性 Agent Teams 任务板 |
