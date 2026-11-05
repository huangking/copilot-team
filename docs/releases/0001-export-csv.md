# 0001-export-csv 发布记录

- 版本 / 提交：待定（以合并后的审阅提交和发布版本为准）
- 环境：PR 验证 → 手动构建验证；当前未授权、未执行生产发布
- 变更范围：为 taskboard CLI 增加 `export --format csv`；变更为纯新增命令，不改变现有命令与存储格式
- 依赖变更（迁移/配置/密钥）：无数据迁移、无新运行时依赖、无新增配置或密钥。CSV 使用 Python 标准库。
- 影响面：taskboard CLI 及基于仓库内容构建的容器镜像；无常驻服务、无生产环境变更。现有 CI 覆盖 lint/test；现有手动 release workflow 只构建镜像并运行 `list` 冒烟，不推送镜像或部署。
- 交付边界：现有工作流与 Dockerfile 已包含源码，无需改动。发布记录范围之外的实现/测试变更须在 PR 审核；本记录不代表发布授权。

## 前置检查与只读核对

| 检查 | 结果 | 说明 |
|---|---|---|
| `make lint` | 通过，退出码 0 | 执行 `python3 -m compileall -q src tests` |
| `make test` | 通过，退出码 0 | `44 passed in 0.35s`；与测试报告的 AC-1..AC-6 全通过结论一致 |
| CI / release workflow | 无需修改 | `.github/workflows/ci.yml` 对 PR 执行 lint 和 pytest；`release.yml` 手动构建镜像并运行 `list` 冒烟。PR 上的实际工作流结果仍须在合并前确认 |
| Dockerfile | 无需修改 | 复制 `src` 并以 `python -m taskboard` 作为入口，新增子命令随源码进入镜像 |
| Docker dry-run | 未完成 | Docker CLI 可用；2026-11-05 再次确认 `docker build --check .` 不受当前 legacy builder 支持（`unknown flag: --check`）。此前普通 `docker build -t taskboard:0001-export-csv .` 因无权访问 `/var/run/docker.sock`（permission denied）失败；没有生成镜像。需在有 Docker daemon 权限的 CI/受控环境验证 |

## 当前交付状态与阻塞项

本记录和本地验证已完成，但**尚不可视为可发布**。以下项目必须由具备相应权限的负责人完成并记录结果：

| 阻塞项 | 当前状态 | 解除条件 |
|---|---|---|
| PR CI | 未验证 | PR 上 `ci.yml` 的 lint 与完整 pytest job 成功；记录 Actions run URL/编号和合并提交 |
| Docker 镜像 | 本地阻塞 | 在 GitHub-hosted runner 或获准访问 Docker daemon 的受控环境运行 release workflow，镜像构建与容器 `list` 冒烟均成功 |
| 发布审批 | 未审批 | 业务负责人和发布负责人批准目标提交、版本、环境与分批计划；将审批链接/时间填入本记录 |
| 真实发布 | 未执行 | 上述三项解除后，按下述步骤由获授权负责人手动触发；本任务不触发工作流、不推送、不部署 |

## 发布步骤

1. 将实现、测试和本发布记录纳入同一 PR；确认范围与规格 `docs/specs/0001-export-csv.md` 一致，并完成代码审查。
2. 等待 PR 上 `.github/workflows/ci.yml` 成功，确认 lint 和完整测试均通过；记录 Actions run URL/编号。本地通过不替代 PR 门禁。
3. 发布负责人确认审批记录已补齐，并选择审阅通过的合并提交及版本号。无审批不执行发布。
4. 在 Actions 中对经批准的版本/提交手动运行现有 `release` workflow；检查镜像构建与 `list` 冒烟均成功。该 workflow 当前不会推送镜像或部署到环境；若需分发镜像，先由负责人确认既有的受控分发方式，不在本任务中新增发布通道。
5. 在有权限的受控环境执行下方 CSV 冒烟检查，核对退出码、stderr 与 stdout 字节；按调用方原有流程分批提供新版本。观察错误报告后再扩大使用范围。此任务不包含生产部署或实际发布执行。

空存储文件路径不存在时，检查 stdout 是否精确为表头加 CRLF（不会创建该存储文件）：

```sh
python3 -c 'import os,subprocess; env=dict(os.environ,PYTHONPATH="src"); p=subprocess.run(["python3","-m","taskboard","--file","/tmp/taskboard-empty-check.json","export","--format","csv"],env=env,capture_output=True); expected=b"id,title,done\\r\\n"; assert (p.returncode,p.stdout,p.stderr)==(0,expected,b""), (p.returncode,p.stdout,p.stderr); print("CSV stdout exact-byte check passed")'
```

对于非空板，针对已知 fixture 抽检完整输出字节（包括字段引号、UTF-8 字节和 CRLF），并确认内容与对应任务及数值 ID 排序一致；不得把错误输出当作 CSV 消费。测试报告中的黑盒样例包括 CR/LF、引号、逗号、Unicode 与乱序 ID。

## 回滚

- 触发条件：PR 门禁失败；构建/冒烟失败；实际调用出现非预期退出码、输出不匹配或用户报告数据解释错误。
- 步骤：停止继续分发新版本；通过原有受控流程回退到上一已批准版本/回退该提交，并确认调用方使用旧版本。发布失败优先回滚，不在生产环境边查边改。
- 数据回滚：不适用。该功能只读已有 JSON 并写 CSV 到 stdout，无数据迁移、无存储格式变更，也不改写存储文件。

## 观测

| 观测项 | 正常范围 | 异常阈值 / 动作 | 看板 / 负责人 |
|---|---|---|---|
| CLI 退出码 | 合法 CSV 导出为 0；参数错误或 AC-6 存储错误为 2 | 任何预期成功输入返回非 0，或意外 Traceback/rc=1：停止扩大发布并回滚/上报 Dev | CLI 调用方 stderr 与进程状态；调用方值班人 |
| stdout 内容 | 表头 `id,title,done`；UTF-8；记录以 CRLF 分隔；`done` 为小写布尔值；抽样字节与预期精确一致 | 多/少记录、排序错误、转义错误、额外诊断混入 stdout：停止消费该导出并上报 Dev | 上述精确字节冒烟命令及调用方抽样；调用方值班人 |
| 错误通道 | 错误信息写 stderr，失败时 stdout 为空 | 错误时产生 CSV 字节或 stderr 无法识别：停止使用并上报 Dev | CLI stderr/调用方日志；调用方值班人 |
| CI 与镜像冒烟 | PR lint/test 成功；镜像构建和 `list` 冒烟成功 | 任一失败不合并/不分发；修复或回滚后重跑 | GitHub Actions run；PR/release 负责人 |

当前 CLI 无集中指标、看板或服务端错误率/P95；由发布负责人在 PR Actions 与调用方抽检中人工观察，不能将“无告警”解释为已观测到零错误。

## 已知风险（Test 报告 R-1..R-4，均为非阻塞但未解决）

| 风险 | 当前表现 | 发布期缓解 | 后续建议 / 责任 |
|---|---|---|---|
| R-1 非法元素导致崩溃 | 合法 JSON 列表含不合规元素时可能出现未捕获异常、Traceback、退出码 1；stdout 为空 | 仅从可信且已知格式正确的任务板导出；若出现 rc=1，停止扩大使用并保留输入样本供 Dev 复现，不在生产边查边改 | PM 决定是否扩展规格/验收标准；Dev 增加输入校验与回归测试 |
| R-2 孤立代理项 | 标题含孤立代理项可能触发 UTF-8 `UnicodeEncodeError`，退出码 1 | 输入来自可信来源；发布前用正常 UTF-8 标题试导出；异常按失败处理 | Dev/PM 评估 JSON 字符串校验及友好错误行为，并补自动化覆盖 |
| R-3 null / 重复 id | `title: null` 可能被输出为 `None`；重复 ID 会重复输出；存储约束未定义 | 导出前核对来源数据；若业务依赖唯一 ID 或非空标题，先在调用方拒绝异常数据，不把 CSV 当规范化/修复工具 | PM 明确存储不变量；Dev 在批准的规格下补校验与测试 |
| R-4 CSV 公式注入 | 标题以 `=`, `+`, `-`, `@` 等开头时，部分表格软件可能将其解释为公式 | 将导出视为不可信文本；告知接收者避免直接在会执行公式的表格软件中打开不可信文件，改用禁用公式解释的导入方式 | PM/安全负责人评估面向用户的缓解；Dev 仅在规格明确后实现安全模式/转义，兼顾原始 CSV 数据语义 |

风险缓解为操作性措施，不表示风险已在代码中修复；不得据此宣称 R-1..R-4 已消除。

## 审批记录（占位，须在任何真实发布前填写）

- PR / 合并提交：待填写
- 发布版本、目标环境及分批计划：待填写
- 业务负责人审批人 / 时间 / 记录链接：待填写
- 发布负责人 / 回滚执行人：待填写
- 审批状态：待审批；未获明确审批不得执行生产发布

## 结果与后续动作

- 开始/结束时间：准备阶段，2026-11-05；未执行真实发布
- 是否发布/回滚：未发布、未回滚
- 验证结果：2026-11-05 本地 `make lint` 通过；`make test` 通过（`44 passed in 0.35s`）；空存储 CSV 精确字节冒烟通过（`id,title,done\r\n`，stderr 为空且不创建存储文件）。Docker 静态检查受 legacy builder 不支持 `--check` 阻塞；PR CI 与受控环境镜像验证待执行
- 后续动作：在 PR 上确认流水线通过；在获批且具备 Docker 权限的环境完成构建/冒烟；由 PM/业务负责人评估 R-1..R-4；补齐审批记录后再决定是否发布
