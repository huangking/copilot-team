# AGENTS.md — 多 Agent 协作契约

> 本文件被 VS Code Copilot（`AGENTS.md` 支持）与 DeepSeek Harness（`agent-instructions`）读取。
> 角色专属流程见 `.agents/skills/`。

## 0. 本仓库

一个刻意保持很小的 Python 任务板：`src/taskboard/` 是纯领域逻辑 + 一个 JSON 文件持久化的 CLI。
当前**故意没有实现 CSV 导出**；`docs/specs/0001-export-csv.md` 是四个角色要一起完成的练习任务。

## 1. 角色与边界

| 角色 | 主要职责 | 可写路径 | 绝对禁止 |
|---|---|---|---|
| PM | 需求澄清、规格、验收标准、任务拆分、委派 | `docs/specs/**`、`docs/backlog/**` | 修改 `src/**`、`tests/**`、CI、部署配置 |
| Dev | 实现、单元测试、重构、修复 | `src/**`、`tests/**` | 修改验收标准、跳过门禁、发布 |
| Test | 独立验证、回归、证据收集 | `tests/**`、`docs/test-reports/**` | 修改 `src/**`（失败只报告） |
| DevOps | CI/CD、镜像与发布、回滚 | `.github/workflows/**`、`Dockerfile`、`docs/releases/**` | 修改业务代码、无审批上生产 |

越界时：**停止并向 PM 报告**，不要"顺手改一下"。

## 2. 交接产物（唯一可信来源）

```
docs/
├── specs/<id>.md          # PM：目标/非目标/验收标准/任务拆分/风险
├── plans/<id>.md          # Dev：改动点/取舍/验证命令
├── test-reports/<id>.md   # Test：用例矩阵/输出/失败复现/覆盖缺口
└── releases/<id>.md       # DevOps：发布步骤/回滚/观测
```

下游开始前必须：读到上游产物且非空 → 在回复里引用路径 → 发现不一致先退回上游。

## 3. 规格的最小内容

- 背景与目标（一句话）
- 非目标
- 验收标准 `AC-1..n`，每条**可被一个命令或一个用例验证**
- 边界与错误场景
- 任务拆分（每项 ≤ 半天，标依赖）
- 风险与回滚思路

## 4. 完成定义（DoD）

- [ ] 每条 `AC-*` 都有自动化验证或明确的人工验证记录
- [ ] `make lint` 与 `make test` 通过
- [ ] 变更范围与 spec 一致，无未解释的额外 diff
- [ ] 有测试报告；失败项有复现步骤或已修复
- [ ] 涉及发布的变更：有回滚步骤与观测项

## 5. 本仓库命令

| 用途 | 命令 |
|---|---|
| 安装测试依赖 | `python3 -m pip install pytest` |
| Lint（语法检查） | `make lint` 或 `python3 -m compileall -q src tests` |
| 单元测试 | `make test` 或 `python3 -m pytest -q` |
| 本地运行 | `PYTHONPATH=src python3 -m taskboard list` |
| 构建镜像 | `docker build -t taskboard:dev .` |

不要引入新的运行时依赖；测试依赖只允许 `pytest`。

## 6. 协作规则

- 一次只做一件事；改动小步、可 review。
- 事实先查代码/文档，查不到再问人。
- 不提交密钥、token、生产地址；`.taskboard.json` 是本地文件，不进 git。
- 不 `git push`、不改发布分支。
- 下游只能看到你写下来的东西：**把决定写进文件，不要只留在对话里**。

## 7. 失败处理

- Dev↔Test 往返 **最多 3 轮**；超过升级给 PM + 人。
- 环境问题（缺依赖、无权限）先记录到产物，再请求人工。
- 规格不可实现 → 立即退回 PM，不要自行改需求。
