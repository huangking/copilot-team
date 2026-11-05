# 0001-export-csv 测试报告

- 环境：Linux；Python 3.14.4；pytest 9.1.1；提交 `6545d9d` + 未提交工作区改动；2026-11-05
- 结论：PASS WITH RISKS

## 基线与执行证据

| 命令 | 实际结果 |
|---|---|
| `make lint` | 退出码 0；输出 `python3 -m compileall -q src tests` |
| `make test` | 退出码 0；`44 passed in 0.52s` |
| `git --no-pager diff --check` | 退出码 0；无输出 |
| `python3 -m pytest -q tests/test_export.py tests/test_export_cli.py tests/test_export_edges.py tests/test_export_errors.py` | 退出码 0；`30 passed in 0.44s` |

验证了当前实现 `src/taskboard/core.py`、`src/taskboard/cli.py`，以及现有交接
`docs/plans/0001-export-csv.md`、`docs/releases/0001-export-csv.md`。本次未改动
`src/**` 或 `tests/**`：现有自动化测试已经覆盖所有验收标准，未发现需补充的真实缺口。

## 用例矩阵

| AC | 场景 | 类型 | 结果 | 证据 |
|---|---|---|---|---|
| AC-1 | 乱序数值 id `10,2`；`true`/`false` 小写；UTF-8；退出码 0 | 自动（真实子进程） | 通过 | `tests/test_export_cli.py::test_cli_exports_sorted_csv_as_utf8_with_rfc4180_quoting`，精确比较 stdout 字节、stderr 和 rc |
| AC-1 | 领域层数值排序与完整精确输出 | 自动 | 通过 | `tests/test_export.py::test_export_csv_sorts_numerically_and_uses_lowercase_booleans` |
| AC-2 | 逗号、双引号、CR、LF、Unicode 分别序列化 | 自动 | 通过 | `tests/test_export.py::test_csv_serializes_special_and_unicode_titles`（5 参数）；精确 CRLF 输出 |
| AC-2 | 混合逗号、CRLF、双引号；所有记录 CRLF 分隔 | 自动（真实子进程） | 通过 | `tests/test_export_cli.py::test_cli_exports_sorted_csv_as_utf8_with_rfc4180_quoting`；预期字节含 `"a,\r\n""quoted"""` 与记录终止 `\r\n` |
| AC-3 | JSON 空列表仅表头且末尾 CRLF | 自动 | 通过 | `tests/test_export.py::test_export_csv_empty_board_ends_with_crlf` |
| AC-3 | 空列表和缺失文件均精确输出表头 CRLF | 自动（真实子进程） | 通过 | `tests/test_export_cli.py::test_cli_exports_only_header_for_empty_or_missing_store`（2 参数） |
| AC-4 | `--format json` 拒绝、rc=2、stdout 为空、stderr 报错 | 自动（真实子进程） | 通过 | `tests/test_export_cli.py::test_cli_rejects_unknown_format_without_stdout` |
| AC-4 | 缺少必填 `--format` 也不输出 CSV | 自动（真实子进程） | 通过 | `tests/test_export_cli.py::test_cli_requires_format_without_stdout` |
| AC-5 | 不存在的存储文件按空板导出 | 自动（真实子进程） | 通过 | `tests/test_export_cli.py::test_cli_exports_only_header_for_empty_or_missing_store` 的 `None` 参数 |
| AC-6 | 无效 JSON `{not json`，stderr 含 `invalid store`、stdout 为空、rc=2 | 自动（真实子进程） | 通过 | `tests/test_export_cli.py::test_cli_reports_invalid_store_without_csv` |
| AC-6 | 顶层 dict（非列表）同样失败 | 自动（真实子进程） | 通过 | 同上参数 `{"not": "a list"}` |
| AC-6 | 空文件、`null`、字符串、数字等坏输入 | 自动 | 通过 | `tests/test_export_edges.py::test_export_non_list_store_values_report_error_without_csv`；`tests/test_export_errors.py::test_export_rejects_invalid_store_without_stdout` |

## 失败项

无。AC-1 至 AC-6 均有自动化覆盖和通过证据。

## 覆盖缺口与风险

- 非阻塞、规格外：合法 JSON 列表中的不合规任务元素（例如 `[1]` 或缺少
  `title`）会在 `TaskBoard.from_dicts` 触发未捕获异常，非 AC-6 所定义的
  “无效 JSON / 顶层非列表”输入。缓解：仅使用符合既有任务存储格式的文件；若要
  支持损坏行，PM 应扩展验收标准后交由 Dev 实现。
- 非阻塞、规格外：孤立 UTF-8 代理项可能在 CLI 编码阶段报
  `UnicodeEncodeError`。缓解：输入应为正常 UTF-8 文本；该输入不属于当前
  JSON 存储契约。
- 未覆盖：Windows 实机行为、大于 10k 任务的性能和 Docker 内运行；前两者不在
  当前 AC 范围，Docker 验证由发布交接在有 daemon 权限的环境完成。
- 未观察到 flaky：每个验证命令各执行一次，均为确定性通过。

## 建议

- 可交给 DevOps 做其发布前检查：没有阻塞性测试失败。
- 这不等同于发布授权；仍需完成 PR CI、Docker/受控环境验证、审批、回滚与观测检查。
