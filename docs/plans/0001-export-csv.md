# 0001-export-csv 实现计划

## 改动点
| 文件 | 改动 | 目的 |
|---|---|---|
| `src/taskboard/core.py` | 以 `csv.writer` 生成按数值 ID 排序、CRLF 分隔的 CSV | 统一 RFC 4180 字段引用与小写布尔值 |
| `src/taskboard/cli.py` | 增加 `export --format csv`，复用现有存储读取及错误处理 | 实现 CLI 导出并避免加载失败时输出 CSV |
| `tests/test_export.py` | 覆盖 AC-1..AC-6 的精确输出、特殊字符及错误路径 | 自动验证验收标准 |

## 关键取舍
- 用标准库 `csv` 而非手工拼接字段，显式设置 CRLF 记录分隔符；UTF-8 编码在 CLI 输出边界处理。
- 复用 argparse `choices` 与既有 `load_board`/`TaskError` 处理，不扩展存储格式或其他命令行为。
- 审视已有实现与测试后，未发现需修改代码的 AC 缺口；不重写既有实现。

## AC → 测试映射
- AC-1：`test_export_csv_sorts_numerically_and_uses_lowercase_booleans`
- AC-2：`test_csv_serializes_special_and_unicode_titles`（逗号、双引号、CR、LF、Unicode）
- AC-3：`test_export_csv_empty_board_ends_with_crlf`
- AC-4：`test_export_rejects_unknown_format_without_stdout`
- AC-5：`test_export_csv_missing_store_is_an_empty_board`
- AC-6：`test_export_invalid_store_reports_error_without_csv`（无效 JSON、非列表）

## 验证命令与结果（2026-11-05）
- `python3 -m pytest tests/test_export.py tests/test_export_cli.py tests/test_export_edges.py tests/test_export_errors.py -q`：通过，`30 passed in 0.38s`。
- `make lint`：通过；输出 `python3 -m compileall -q src tests`，退出码 0。
- `make test`：通过；`44 passed in 0.39s`。
- `git diff --check`：通过；无空白错误。

交给 Test：AC-1..AC-6 已由 `tests/test_export.py` 覆盖，并由
`tests/test_export_cli.py`、`tests/test_export_edges.py` 和
`tests/test_export_errors.py` 补充黑盒 CLI 与边界验证；当前实现无需额外修复。
全量测试数高于 `docs/test-reports/0001-export-csv.md` 的历史快照（`25 passed`），
因为当前工作区还包含补充的 `tests/test_export_*.py` 用例；该独立测试报告未由 Dev 修改。

## 风险
- 特殊字符可能破坏 CSV 字段或记录边界；特殊字符用例断言精确序列化结果。
- 存储错误不应混入标准输出；AC-4/AC-6 用例同时核对输出通道与退出码。
