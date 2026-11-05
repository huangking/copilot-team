# 并行实施手册（VS Code + Copilot）

目标：不改角色链的前提下，把"能并行的部分"真正跑起来。

先记住一条：**`PM → Dev → Test → DevOps` 这条链是串行的**，并行发生在"任务之间"或"一次评审的内部"。
四条路径，按风险从低到高：

| 路径 | 需要 worktree | 会改代码 | 第一次耗时 | 适合 |
|---|---|---|---|---|
| 1. 并行评审 | 否 | 否 | 5 分钟 | 任何 diff |
| 2. 并行测试切片 | 否 | 只写新测试文件 | 10 分钟 | 实现已完成 |
| 3. 并行实现（变体/独立任务） | 是 | 是 | 30 分钟 | 方案对比、独立 feature |
| 4. 云端并行 | 否（远程） | 是（PR） | 30 分钟+ | 多个 issue |

---

## 0. 前置检查

1. VS Code 1.106+，已装 GitHub Copilot Chat，已登录。
2. 打开 `/data/project/copilot-team`，确认 Chat 的 agent 下拉里能看到 **PM / Dev / Test / DevOps / Review Lead**。
   看不到就跑命令面板 **Chat: Diagnostics**，看 `.github/agents` 是否加载、工具名有没有告警。
3. 确认基线：

   ```bash
   make test        # 应为 25 passed（含你本地未提交的 export 实现）
   git status       # 先看清楚哪些改动还没提交
   ```

4. **第 3 条路径开始前必须先提交或 stash**：worktree 是从 `HEAD` 建的，不会带上未提交改动。

   ```bash
   git add -A && git commit -m "feat: csv export"   # 或 git stash push -u
   ```

---

## 1. 并行评审（5 分钟，零风险）

适合：当前这轮 CSV 实现还没合并，想先让四个视角同时挑毛病。

1. Chat 里把 agent 切到 **Review Lead**。
2. 输入：

   ```text
   用 changes 列出当前改动，评审这些文件（含未跟踪的 tests/test_export.py、
   docs/plans、docs/test-reports、docs/releases）。
   按正确性 / 安全 / 性能 / 兼容四个角度并行评审，最后汇总成一张表。
   ```

3. Review Lead 会启动 4 个 **Reviewer** 子代理，界面上是 4 个可展开的工具调用；全部返回后给结论。
   Review Lead 没有终端，看不了 `git diff`；它会按当前文件内容评审。要看真实 diff，就先把 diff 粘进对话，或改用内置 **Agent** 组织评审。
4. 产物：一份 `blocker / major / minor` 表格；点 **修复发现** 可以交给 Dev。

确认真的并行：展开子代理调用，应该能看到多个 Reviewer 同时处于 running，而不是逐个完成。

如果 Review Lead 调不动 Reviewer：custom agent 作为 subagent 目前是实验特性。退路是让 Review Lead 自己按四个角度顺序评审，或者临时把 `reviewer.agent.md` 的 `user-invokable` 改成 `true`，开 4 个会话各评一个角度。

---

## 2. 并行测试切片（10 分钟，同一工作区）

适合：实现已完成，需要补不同面的测试；只写新文件，互不冲突。

1. 开 3 个会话（Chat 顶部 `+` → Local），每个都选 **Test** agent。
2. 三个 prompt 分别只允许写一个**新文件**：

   ```text
   会话 A：只为 CSV 导出补"边界值"测试，只创建 tests/test_export_edges.py。
   覆盖空标题、超长标题、Unicode、CR/LF；不要改 src/**，不要改其他测试文件。
   ```

   ```text
   会话 B：只为 CSV 导出补"错误路径"测试，只创建 tests/test_export_errors.py。
   覆盖无效 JSON、顶层不是列表、非法 --format；不要改 src/**。
   ```

   ```text
   会话 C：只为 CSV 导出补"CLI 合约"测试，只创建 tests/test_export_cli.py。
   断言 stdout/stderr/退出码；不要改 src/**。
   ```

3. 三个会话可以同时跑。跑测试时用：

   ```bash
   python3 -m pytest -q -p no:cacheprovider
   ```

   `-p no:cacheprovider` 避免多个 pytest 进程抢 `.pytest_cache`。

4. 汇总：三个新文件互不重叠，直接 `git add tests/test_export_*.py` 一起提交。

注意：不要让任何 Test 会话改 `src/**`；Test 的 persona 已经这么要求，prompt 里再强调一次。

---

## 3. 并行实现：worktree（30 分钟）

有两种用法：

- **变体对比**：同一个任务，两种实现思路，各开一个 worktree，最后选一个合并。
- **独立任务**：写作用域完全不重叠的任务，各开一个 worktree，最后依次合并。

`core.py` / `cli.py` 是共享入口，**同一 feature 的多个写任务不要并行**；变体对比不受此限制（最后只选一个）。

### 3.1 建 worktree

在仓库根目录：

```bash
scripts/parallel-worktrees.sh create due-a due-b
```

默认建在 `../copilot-team.worktrees/<name>`，分支 `parallel/<name>`，基于 `HEAD`。
输出会打印每个目录的 `code` 命令。

```bash
scripts/parallel-worktrees.sh list      # 确认
```

### 3.2 每个 worktree 一个窗口

```bash
code ../copilot-team.worktrees/due-a
code ../copilot-team.worktrees/due-b
```

每个窗口是独立的 workspace，Chat 的 sessions list 也各自独立，互不干扰。

### 3.3 每个窗口开一个会话

选 **Dev**，prompt 必须写清写作用域与交付：

```text
任务：给任务板加 due date（方案 A：ISO 字符串存储）。
写作用域：只允许改 src/taskboard/core.py、src/taskboard/cli.py、tests/test_due.py。
约束：不引入新依赖；保持现有 JSON 存储兼容；先写 docs/plans/due-a.md 再改代码。
交付：make test 全绿 + 贴实际输出。
```

另一个窗口换成方案 B（例如 datetime + 序列化器），其余相同。

### 3.4 各自提交

每个窗口：

```bash
git add -A
git commit -m "feat: due date (approach A)"
make test
```

### 3.5 对比与合并

回到主工作区（`/data/project/copilot-team`）：

```bash
git diff main..parallel/due-a --stat
git diff main..parallel/due-b --stat
git log --oneline main..parallel/due-a
```

选定一个后：

```bash
git merge --no-ff parallel/due-a
make test
```

变体 B 直接丢弃：

```bash
git worktree remove ../copilot-team.worktrees/due-b
git branch -D parallel/due-b
```

### 3.6 独立任务的合并顺序

如果两个任务真的是独立文件（比如 `src/taskboard/export/csv.py` 与 `src/taskboard/export/json.py`）：

```bash
git merge --no-ff parallel/task-a
make test
git merge --no-ff parallel/task-b
make test
```

先合谁写进 spec 的并行批次表；冲突由"集成者"统一解决，不要让两个 agent 互相 rebase。

---

## 4. 云端并行（issue → PR）

适合：规格已经稳定、可以等几十分钟、想要独立 PR 的场景。

1. 每个任务一个 issue，body 直接放 spec 的验收标准：

   ```bash
   gh issue create --title "CSV export: edge cases" --body-file docs/specs/0001-export-csv.md
   ```

2. 在 GitHub issue 页面右侧 **Assignees → Copilot**（或在评论里 `@copilot` 说明要实现哪部分）。
3. 每个 issue 会独立开一个 agent session，产出独立 PR。
4. 在 VS Code 的 sessions list 里能看到这些云端会话；PR 之间仍会有合并冲突，按批次顺序合并。

并发额度受套餐限制，超出会排队；不要一次开十几个。

---

## 5. 怎么确认"真的并行了"

| 路径 | 观察点 |
|---|---|
| 并行评审 | 子代理调用同时 running；总耗时接近最慢的那个，而不是四个之和 |
| 多会话 | sessions list 里多个会话同时显示 in-progress |
| worktree | `git worktree list` 有两条以上；两个窗口各自能独立 `make test` |
| 云端 | 同一时间有多个 agent session / 多个 PR |

---

## 6. 常见问题

**Q：两个本地会话改同一文件会怎样？**
后写的覆盖先写的；编辑器里可能看到对方的中间状态。要么分工到不同文件，要么用 worktree。

**Q：worktree 里看不到我刚写的代码？**
worktree 从 `HEAD` 建，未提交改动不会带过去。先 commit 或 stash。

**Q：并行后更慢了？**
常见原因：任务拆分粒度太细、review 带宽不够、模型限流。先降到 2 路。

**Q：handoff 能不能并行？**
不能。handoff 是同一会话的顺序交接，设计上就是人工审批门。要并行只能在任务层拆，或在一个 agent 内部用 subagent fan-out。

**Q：Reviewer 不出现在下拉框？**
这是刻意的：`user-invokable: false`，只作为 Review Lead 的子代理。要单独用就临时改成 `true`。

---

## 7. 一页检查单

- [ ] 当前改动已提交或 stash（worktree 路径必须）
- [ ] 每个并行任务写明"只允许改哪些路径"
- [ ] 任意两个任务的写作用域没有交集（变体对比除外）
- [ ] 每个 worktree 单独 `make test` 通过后再合并
- [ ] 合并后主工作区再跑一次 `make lint && make test`
- [ ] 并行数 ≤ 3，先验证收益再加
